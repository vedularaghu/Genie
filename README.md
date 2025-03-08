# Genie - Document Intelligence

Genie is a web application that allows users to upload documents (PDF, Excel, CSV) and ask questions about them. The application uses a Retrieval-Augmented Generation (RAG) system to provide accurate answers based on the content of the uploaded documents.

## Mistral OCR Support

Genie now includes Optical Character Recognition (OCR) capabilities powered by Mistral AI. To use OCR features:
- Add your Mistral API key to the `.env` file
- Upload PDF documents that contain text or images with text
- Ask questions that include "OCR" in your query to trigger OCR processing

## Features

- Upload and process PDF, Excel, and CSV files (up to 10GB per file)
- OCR support for extracting text from images in PDFs
- Ask questions about your documents in natural language
- View and manage your uploaded documents
- Contextual conversation with memory of previous interactions

## Tech Stack

- **Backend**: Flask, LangChain, LangGraph
- **Frontend**: React, CSS
- **AI**: OpenAI GPT-4o, Text Embedding 3 Large, Mistral AI OCR

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=<your-openai-api-key>
   MISTRAL_API_KEY=<your-mistral-api-key>
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=<your-langchain-api-key>
   ```
5. Run the backend server:
   ```
   python server.py
   ```
6. In a separate terminal, navigate to the frontend directory and run:
   ```
   cd frontend
   npm install
   npm start
   ```
7. Open your browser and navigate to `http://localhost:3000`

## Usage

1. Upload your documents through the Documents tab
2. Switch to the Chat tab to ask questions about your documents
3. The system will retrieve relevant information from your documents and provide answers
4. For OCR processing, include the word "OCR" in your query when asking about PDF documents

## Project Structure

- `server.py`: Flask web server and API endpoints
- `rag_service.py`: RAG system implementation using LangChain and LangGraph
- `frontend/`: React frontend application
- `docs/`: Directory where uploaded documents are stored