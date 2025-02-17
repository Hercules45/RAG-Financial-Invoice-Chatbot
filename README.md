# Financial Invoice Analysis Chatbot

**This Flask application provides an interactive chatbot interface for analyzing financial invoices.** It leverages the power of Large Language Models (LLMs) to answer questions about uploaded invoice data. The application supports a variety of file formats, performs OCR on images, and uses a vector database for efficient context retrieval.

## Features

*   **Multiple File Formats:** Supports uploading `.txt`, `.csv`, `.xlsx`, `.xls`, `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, and `.png` files.
*   **Automated OCR:** Performs Optical Character Recognition (OCR) on image files (JPEG, PNG) to extract text.
*   **Flexible Document Loading:** Uses Langchain's document loaders (`TextLoader`, `CSVLoader`, `UnstructuredExcelLoader`, `UnstructuredWordDocumentLoader`, `PyPDFLoader`) to handle different file types.
*   **Intelligent Text Splitting:** Employs `RecursiveCharacterTextSplitter` to divide documents into manageable chunks for the LLM, respecting sentence and paragraph boundaries.
*   **Vector Database (ChromaDB):** Stores document embeddings in a ChromaDB vector database for efficient similarity search and context retrieval.
*   **MultiQuery Retrieval:** Uses Langchain's `MultiQueryRetriever` to generate multiple queries from the user's input, improving retrieval accuracy and providing more comprehensive results.
*   **Google Gemini 1.5 Flash Integration:** Utilizes Google's Gemini 1.5 Flash model (via `langchain-google-genai`) for powerful question answering.
*   **Safety Filters:** Implements safety settings to block harmful or inappropriate content.
*   **Interactive Web Interface:** Provides a user-friendly chat interface built with Flask, HTML, CSS, and JavaScript.
*   **Source Document Display:** Shows relevant snippets from the source document alongside the chatbot's response in a sidebar.
*   **Processing Status and Loading Bar:** Displays a loading bar and updates the user on the processing status of uploaded files.
*   **Dark Mode Support:** Includes a toggle to switch between light and dark themes.
*   **Collapsible Sidebar:** Features a sidebar to display chat history and source documents, which can be collapsed to maximize chat space.
*   **File and ChromaDB cleanup:** Cleans up uploaded files and ChromaDB collections after 24 hours.
  

## Demo

Here's a short demonstration of the chatbot in action:

![Chatbot Demo](RAG%20PROJECT/assets/chatbot_demo.gif)


## Requirements

*   **Python 3.7+**
*   **Tesseract OCR (for image processing):**  This is *not* a Python package.  See installation instructions below.
*   **Google API Key:**  You'll need a Google API key with access to the Generative Language API and the embeddings API.

## Installation

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/Hercules45/RAG-Financial-Invoice-Chatbot.git
    cd RAG-Financial-Invoice-Chatbot/RAG\ PROJECT
    ```

2.  **Install Tesseract OCR (External Dependency):**

    *   **Windows:** Download and install from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).  **Important:** Add the Tesseract installation directory to your system's `PATH` environment variable.
    *   **macOS:**  Use Homebrew: `brew install tesseract`
    *   **Linux (Debian/Ubuntu):**  `sudo apt-get install tesseract-ocr`
    *   **Linux (Fedora/CentOS/RHEL):** `sudo yum install tesseract`

3.  **Create a Virtual Environment (Strongly Recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Python Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up Your Google API Key (Securely):**

    *   Obtain a Google API key.
    *   **Recommended Method (Using .env):**
        *   Create a file named `.env` in the `RAG PROJECT` directory.
        *   Add the following line to the `.env` file, replacing `your-api-key` with your actual key:

            ```
            GOOGLE_API_KEY=your-api-key
            ```
        *   **Important:** Add `.env` to your `.gitignore` file to prevent your API key from being committed to the repository.  Create a `.gitignore` file in the `RAG-Financial-Invoice-Chatbot` directory (if one doesn't already exist) and add the following lines:
            ```
            .env
            venv/
            uploads/
            ```


## Running the Application

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000/` in your web browser.


## Usage

1.  **Upload an Invoice:** Click the upload button (paperclip icon) and select your invoice file.
2.  **Wait for Processing:** A loading bar will indicate the progress.  The application extracts text, creates embeddings, and initializes the LLM.  The `chroma_db` directory will be created inside `uploads` during this process.
3.  **Ask Questions:** Once processing is complete, type your questions about the invoice in the chat input box and press Enter.
4.  **View Source Documents:** The sidebar displays snippets from the source document that are relevant to the chatbot's answer.  You can collapse the sidebar for more chat space.


## Project Structure

*   **`app.py`:** The main Flask application file (backend logic).
*   **`static/`:**  Contains static assets.
    *   **`styles.css`:**  CSS stylesheet.
    *   **`script.js`:**  JavaScript code for frontend interactions.
    *   **`user-avatar.png`:** Placeholder image for user avatars.
    *   **`ai-avatar.png`:** Placeholder image for AI avatars.
*   **`templates/`:**  Contains HTML templates.
    *   **`index.html`:** The main HTML template for the chatbot interface.
*   **`uploads/`:**  Temporary storage for uploaded files (files are deleted after 24 hours).  **Note:** The `chroma_db` directory is created *inside* this `uploads` directory dynamically when a file is processed.
*   **`assets/`:** Contains assets such as images and GIFs.
*   **`requirements.txt`:**  Lists the required Python dependencies.
*   **`.env`:** (Not provided here, but highly recommended) Stores environment variables (e.g., your Google API key).

