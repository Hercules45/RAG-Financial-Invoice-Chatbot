from flask import Flask, request, jsonify, render_template, send_from_directory, session
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, UnstructuredExcelLoader,UnstructuredWordDocumentLoader
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
from werkzeug.utils import secure_filename
import os
import re
import traceback
import pytesseract
from PIL import Image
import uuid
import threading
import time
import shutil
import schedule

from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs("chroma_db", exist_ok=True)

processing_lock = threading.Lock()
processing_status = {}  # Dictionary to track processing status
qa_chain = None  # Global variable to store the current QA chain

# --- Cleanup Functions ---
def cleanup_uploads(older_than_seconds=86400):  # 24 hours
    """Deletes old files from the uploads directory."""
    uploads_path = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(uploads_path):
        file_path = os.path.join(uploads_path, filename)
        if os.path.isfile(file_path):
            last_modified_time = os.path.getmtime(file_path)
            if time.time() - last_modified_time > older_than_seconds:
                try:
                    os.remove(file_path)
                    app.logger.info(f"Deleted old upload: {filename}")
                except Exception as e:
                    app.logger.error(f"Error deleting upload {filename}: {e}")

def cleanup_chroma_db(older_than_seconds=86400):  # 24 hours
    """Deletes old Chroma collections from the chroma_db directory."""
    chroma_db_path = "chroma_db"
    for dir_name in os.listdir(chroma_db_path):
        if dir_name.startswith("rag_"):
            dir_path = os.path.join(chroma_db_path, dir_name)
            if os.path.isdir(dir_path):
                last_modified_time = os.path.getmtime(dir_path)
                if time.time() - last_modified_time > older_than_seconds:
                    try:
                        shutil.rmtree(dir_path)  # Delete the directory and its contents
                        app.logger.info(f"Deleted old Chroma collection: {dir_name}")
                    except Exception as e:
                        app.logger.error(f"Error deleting Chroma collection {dir_name}: {e}")
# --- end of cleanup functions---

def generate_unique_filename(filename):
    """Generate UUID-based filename to prevent conflicts"""
    return f"{uuid.uuid4().hex[:8]}_{secure_filename(filename)}"

def initialize_qa_system(filename):
    global processing_status, qa_chain
    with processing_lock:
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_ext = os.path.splitext(filename)[1].lower()
            temp_ocr_file = None

            # Handle different file types
            if file_ext in ['.jpg', '.jpeg', '.png']:
                # OCR Processing with cleanup
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
                temp_ocr_file = f"ocr_{uuid.uuid4().hex[:8]}.txt"
                ocr_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_ocr_file)
                with open(ocr_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                loader = TextLoader(ocr_path)
            else:
                # Standard document loaders
                if file_ext == '.txt':
                    loader = TextLoader(file_path, encoding='utf-8')
                elif file_ext == '.csv':
                    loader = CSVLoader(file_path)
                elif file_ext in ['.xlsx', '.xls']:
                    loader = UnstructuredExcelLoader(file_path)
                elif file_ext == '.pdf':
                    loader = PyPDFLoader(file_path)
                elif file_ext in ['.docx', '.doc']: 
                    loader = UnstructuredWordDocumentLoader(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")

            documents = loader.load()

            # Cleanup OCR temp file immediately after loading
            if temp_ocr_file:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], temp_ocr_file))
                except Exception as e:
                    app.logger.error(f"OCR cleanup failed: {str(e)}")

            # Text splitting
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            texts = text_splitter.split_documents(documents)

            # Simulate processing stages for the loading bar
            processing_status[filename] = "processing"
            time.sleep(2)  # Simulate the first stage of processing

            # Initialize embeddings 
            embeddings = GoogleGenerativeAIEmbeddings(
                model='models/text-embedding-004',
                google_api_key=os.environ.get('GOOGLE_API_KEY'),
                task_type="retrieval_query",
                timeout=120  # Set timeout to 120 seconds
            )

            # Create unique Chroma collection
            collection_name = f"rag_{uuid.uuid4().hex[:8]}"
            vectordb = Chroma.from_documents(
                documents=texts,
                embedding=embeddings,
                collection_name=collection_name,
                persist_directory=f"chroma_db/{collection_name}"
            )

            time.sleep(2)  # Simulate the second stage of processing
            processing_status[filename] = "processing_2"
            time.sleep(2)  # Simulate the third stage of processing
            processing_status[filename] = "processing_3"

            # Prompt template
            prompt_template = """
            You are a financial assistant specializing in invoice analysis. Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

            Context: {context}
            Question: {question}
            Answer:
            """
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=['context', 'question']
            )

            # Safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            }

            # Initialize chat model
            chat_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.environ.get('GOOGLE_API_KEY'),
                temperature=0.7,
                safety_settings=safety_settings
            )

            # Create QA chain with MultiQueryRetriever
            retriever = MultiQueryRetriever.from_llm(
                retriever=vectordb.as_retriever(search_kwargs={"k": 5}),
                llm=chat_model
            )

            qa_chain = RetrievalQA.from_chain_type(
                llm=chat_model,
                retriever=retriever,
                return_source_documents=True,
                chain_type="stuff",
                chain_type_kwargs={"prompt": prompt}
            )

            processing_status[filename] = "completed"  # Mark as completed

            return qa_chain

        except Exception as e:
            app.logger.error(f"Initialization Error: {str(e)}\n{traceback.format_exc()}")
            processing_status[filename] = "failed"
            raise

def is_greeting(text):
    greetings = ['hi', 'hello', 'hey', 'how are you', 'greetings']
    return any(re.search(r'\b' + greeting + r'\b', text.lower()) for greeting in greetings)

@app.route("/upload", methods=["POST"])
def upload_file():
    global qa_chain
    app.logger.info("File upload request received")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Generate unique filename and save
        original_name = secure_filename(file.filename)
        unique_name = generate_unique_filename(original_name)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        
        # Clean previous upload and reset qa_chain
        if 'filename' in session:
            try:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], session['filename'])
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                app.logger.error(f"Cleanup error: {str(e)}")
            qa_chain = None  # Invalidate the old QA chain
        
        file.save(file_path)
        session['filename'] = unique_name
        return jsonify({"message": "File uploaded successfully"})
        
    except Exception as e:
        app.logger.error(f"Upload Error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": f"File upload failed: {str(e)}"}), 500

@app.route("/process", methods=["POST"])
def process_file():
    global processing_status, qa_chain
    if 'filename' not in session:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        filename = session['filename']
        processing_status[filename] = "started"

        # Start processing in a separate thread
        def process_in_background(filename):
            global qa_chain
            qa_chain = initialize_qa_system(filename)

        thread = threading.Thread(target=process_in_background, args=(filename,))
        thread.start()

        return jsonify({"message": "Processing started"})

    except Exception as e:
        app.logger.error(f"Processing Error: {str(e)}\n{traceback.format_exc()}")
        processing_status[filename] = "failed"
        return jsonify({"error": f"File processing failed: {str(e)}"}), 500

@app.route("/processing_status", methods=["GET"])
def get_processing_status():
    filename = session.get('filename')
    if not filename:
        return jsonify({"status": "not started"})
    status = processing_status.get(filename, "not started")
    return jsonify({"status": status})

@app.route("/", methods=["GET", "POST"])
def index():
    global qa_chain
    if request.method == "POST":
        if 'question' in request.form:
            user_question = request.form["question"]

            if is_greeting(user_question):
                if 'filename' in session:
                    bot_response = "Hello! I'm here to help with your financial invoice queries. What would you like to know about the uploaded invoice?"
                else:
                    bot_response = "Hello! I'm here to help with financial invoice analysis. Please upload an invoice file (text, CSV, Excel, image, or PDF) for me to analyze. What would you like to know?"
                return jsonify({"bot_response": bot_response, "source_documents": []})

            if 'filename' not in session:
                return jsonify({"bot_response": "Please upload a file first", "source_documents": []})

            if qa_chain is None:
                return jsonify({"bot_response": "The QA system is not initialized yet. Please wait for the file to be processed.", "source_documents": []})

            try:
                
                response = qa_chain.invoke({"query": user_question})
                return jsonify({
                    "bot_response": response['result'],
                    "source_documents": [doc.page_content[:200]+"..." for doc in response.get('source_documents', [])]
                })
            except Exception as e:
                app.logger.error(f"Query Error: {str(e)}\n{traceback.format_exc()}")
                return jsonify({"bot_response": f"Error: {str(e)}", "source_documents": []}), 500

    return render_template("index.html")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Test successful"}), 200

# --- Scheduler Thread ---
def run_scheduled_jobs():
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Define scheduled tasks (every 24 hours)
schedule.every(24).hours.do(cleanup_uploads)
schedule.every(24).hours.do(cleanup_chroma_db)

# Start the scheduler thread in the background
scheduler_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
scheduler_thread.start()


if __name__ == "__main__":
    # cleanup_uploads()
    # cleanup_chroma_db()
    # app.run(debug=True, use_reloader=False)

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
