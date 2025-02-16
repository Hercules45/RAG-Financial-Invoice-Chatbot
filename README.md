# Financial Invoice Analysis Chatbot

**This Flask application provides an interactive chatbot interface for analyzing financial invoices.** It leverages the power of Large Language Models (LLMs) to answer questions about uploaded invoice data. The application supports a variety of file formats, performs OCR on images, and uses a vector database for efficient context retrieval.

## Features

*   **Multiple File Formats:** Supports uploading `.txt`, `.csv`, `.xlsx`, `.xls`, `.pdf`, `.jpg`, `.jpeg`, and `.png` files.
*   **Automated OCR:** Performs Optical Character Recognition (OCR) on image files (JPEG, PNG) to extract text.
*   **Flexible Document Loading:** Uses Langchain's document loaders (`TextLoader`, `CSVLoader`, `UnstructuredExcelLoader`, `PyPDFLoader`) to handle different file types.
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
*   **Responsive Design:** Adapts the layout for optimal viewing on different screen sizes (desktop, mobile).

## Requirements

*   **Python 3.7+**
*   **Tesseract OCR (for image processing):**  This is *not* a Python package.  See installation instructions below.
*   **Google API Key:**  You'll need a Google API key with access to the Generative Language API and the embeddings API.

## Installation

1.  **Clone the Repository:**

    ```bash
    git clone <your_repository_url>
    cd <your_repository_directory>
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
        *   Create a file named `.env` in the project's root directory.
        *   Add the following line to the `.env` file, replacing `your-api-key` with your actual key:

            ```
            GOOGLE_API_KEY=your-api-key
            ```

        *   **Important:**  *Do not* commit your `.env` file to version control (add it to your `.gitignore`).


## Running the Application

```bash
python app.py
