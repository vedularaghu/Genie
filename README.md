# Genie - Document Intelligence

Genie is a web application that allows users to upload documents (PDF, Excel, CSV) and ask questions about them using natural language. The application uses a Retrieval-Augmented Generation (RAG) system to provide accurate answers based on the content of the uploaded documents.

## Features

- Upload and process PDF, Excel, and CSV files (up to 10GB per file)
- Ask questions about your documents in natural language
- View and manage your uploaded documents
- Contextual conversation with memory of previous interactions

## Tech Stack

- **Backend**: Flask, LangChain, LangGraph
- **Frontend**: HTML, CSS, JavaScript
- **AI**: OpenAI GPT-4o, Text Embedding 3 Large

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=<open-ai-apio>
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=<lang-chain-api>
   ```
5. Run the application:
   ```
   python server.py
   ```
6. Open your browser and navigate to `http://localhost:8080`

## Usage

1. Upload your documents through the Documents tab
2. Switch to the Chat tab to ask questions about your documents
3. The system will retrieve relevant information from your documents and provide answers

## Project Structure

- `server.py`: Flask web server and API endpoints
- `rag_service.py`: RAG system implementation using LangChain and LangGraph
- `templates/`: HTML templates for the web interface
- `docs/`: Directory where uploaded documents are stored