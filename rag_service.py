import os
import dotenv
import uuid
import glob
import base64
from pathlib import Path
import tempfile
from typing import List, Dict, Any
import requests
from PIL import Image
import io
import re
import threading
import time
import concurrent.futures

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

dotenv.load_dotenv(Path(__file__).parent / ".env")

_llm = None
_embeddings = None
_vector_store = None
_chain = None
_is_initialized = False
_memory = MemorySaver()
_conversation_history = {}

# Global timeout settings
_default_timeout = 30  # Default timeout in seconds

def load_documents():
    """Load documents from the docs directory, supporting PDF, Excel, and CSV."""
    docs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    if not os.path.exists(docs_directory):
        os.makedirs(docs_directory)
    
    print(f"Loading documents from: {docs_directory}")
    all_documents = []
        
    pdf_files = glob.glob(os.path.join(docs_directory, "**/*.pdf"), recursive=True)
    print(f"Found {len(pdf_files)} PDF files")
    for pdf_path in pdf_files:
        try:
            print(f"Loading PDF: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            print(f"  - Loaded {len(docs)} pages from PDF: {os.path.basename(pdf_path)}")
            
            for doc in docs:
                if hasattr(doc, 'metadata'):
                    doc.metadata['source'] = os.path.basename(pdf_path)
                    doc.metadata['file_type'] = 'pdf'
            
            all_documents.extend(docs)
        except Exception as e:
            print(f"Error loading {pdf_path}: {str(e)}")
    
    excel_files = glob.glob(os.path.join(docs_directory, "**/*.xlsx"), recursive=True)
    excel_files.extend(glob.glob(os.path.join(docs_directory, "**/*.xls"), recursive=True))
    print(f"Found {len(excel_files)} Excel files")
    for excel_path in excel_files:
        try:
            print(f"Loading Excel: {excel_path}")
            loader = UnstructuredExcelLoader(excel_path, mode="elements")
            docs = loader.load()
            print(f"  - Loaded {len(docs)} elements from Excel: {os.path.basename(excel_path)}")
            
            for doc in docs:
                if hasattr(doc, 'metadata'):
                    doc.metadata['source'] = os.path.basename(excel_path)
                    doc.metadata['file_type'] = 'excel'
            
            all_documents.extend(docs)
        except Exception as e:
            print(f"Error loading {excel_path}: {str(e)}")
        
    csv_files = glob.glob(os.path.join(docs_directory, "**/*.csv"), recursive=True)
    print(f"Found {len(csv_files)} CSV files")
    for csv_path in csv_files:
        try:
            print(f"Loading CSV: {csv_path}")
            loader = CSVLoader(csv_path)
            docs = loader.load()
            print(f"  - Loaded {len(docs)} rows from CSV: {os.path.basename(csv_path)}")
            
            for doc in docs:
                if hasattr(doc, 'metadata'):
                    doc.metadata['source'] = os.path.basename(csv_path)
                    doc.metadata['file_type'] = 'csv'
            
            all_documents.extend(docs)
        except Exception as e:
            print(f"Error loading {csv_path}: {str(e)}")
    
    print(f"Total documents loaded: {len(all_documents)}")
    return all_documents

def split_documents(documents):
    """Split documents into chunks."""
    if not documents:
        print("No documents to split")
        return []
    
    # Use a simple splitter for all document types
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks")
    return chunks

def initialize_system():
    """Initialize a simple RAG system."""
    global _llm, _embeddings, _vector_store, _chain, _is_initialized
    
    if _is_initialized:
        return _chain
    
    print("Initializing simple RAG system...")
    
    # Initialize LLM
    _llm = ChatOpenAI(model="gpt-4o", temperature=0)
    print("LLM initialized")
    
    # Initialize embeddings
    _embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    print("Embeddings initialized")
    
    # Create vector store
    _vector_store = InMemoryVectorStore(embedding=_embeddings)
    print("Vector store initialized")
    
    # Load documents
    documents = load_documents()
    
    # Process documents
    if documents:
        chunks = split_documents(documents)
        if chunks:
            print(f"Adding {len(chunks)} chunks to vector store...")
            _vector_store.add_documents(documents=chunks)
            print("Documents added to vector store")
    else:
        print("WARNING: No documents were loaded")
    
    # Create a simple RAG chain
    def simple_rag_chain(query, thread_id=None):
        # Retrieve relevant documents
        docs = _vector_store.similarity_search(query, k=5)
        
        # Format documents
        context = ""
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', '')
            page_info = f" (page {page})" if page else ""
            
            context += f"\n\nDocument {i+1} from {source}{page_info}:\n{doc.page_content}"
        
        # Create prompt
        prompt = f"""You are a document analysis assistant. Answer the question based ONLY on the following context from documents.

Context:
{context}

Question: {query}

Important instructions:
1. Only use information from the provided context
2. If the answer is not in the context, say "I don't have enough information to answer this question based on the provided documents."
3. Do not use your general knowledge
4. Cite the document sources in your answer

Answer:"""
        
        # Generate response
        response = _llm.invoke(prompt)
        return response.content
    
    _chain = simple_rag_chain
    _is_initialized = True
    print("Simple RAG system initialized")
    return _chain

def process_with_timeout(func, args=(), kwargs={}, timeout=None):
    """Execute a function with a timeout."""
    if timeout is None or timeout <= 0:
        # No timeout, just execute the function
        return func(*args, **kwargs)
    
    # Use concurrent.futures to run the function with a timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"Processing timed out after {timeout} seconds")
            return "I'm sorry, but processing your request took too long and was stopped. Please try a simpler question or adjust the timeout setting."

def process_query(query, thread_id=None, timeout=None):
    """Process a user query and return the response with timeout support."""
    if not _is_initialized:
        initialize_system()
    
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    # Extract timeout from query if specified
    timeout_match = re.search(r'timeout=(\d+)', query)
    if timeout_match:
        try:
            user_timeout = int(timeout_match.group(1))
            timeout = user_timeout
            # Remove the timeout parameter from the query
            query = re.sub(r'timeout=\d+', '', query).strip()
        except ValueError:
            pass
    
    try:
        # Check if this is an OCR request
        ocr_result = process_ocr_request(query, thread_id)
        if ocr_result:
            return ocr_result
        
        # Get the list of document filenames
        document_files = get_document_list()
        
        if not document_files:
            print("WARNING: No documents have been loaded.")
            return {
                "response": "I don't have any documents in my knowledge base yet. Please upload some documents first.",
                "thread_id": thread_id,
                "success": True
            }
        
        # Special handling for document existence queries
        if "any document" in query.lower() or "have document" in query.lower():
            doc_list = ", ".join(document_files)
            response = f"I have {len(document_files)} document(s) in my knowledge base: {doc_list}."
            
            return {
                "response": response,
                "thread_id": thread_id,
                "success": True
            }
        
        print(f"Processing query: '{query}' with timeout: {timeout if timeout else 'None'}")
        
        # Run the chain with timeout
        if timeout:
            response = process_with_timeout(_chain, args=(query, thread_id), timeout=timeout)
        else:
            response = _chain(query, thread_id)
        
        # If response is a string (from timeout), wrap it
        if isinstance(response, str):
            return {
                "response": response,
                "thread_id": thread_id,
                "success": True
            }
        
        print(f"Response generated successfully")
        return {
            "response": response,
            "thread_id": thread_id,
            "success": True
        }
    except Exception as e:
        print(f"Error in process_query: {str(e)}")
        return {
            "response": f"Error processing query: {str(e)}",
            "thread_id": thread_id,
            "success": False
        }

def get_document_list():
    """Get list of all supported documents in the docs directory."""
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    documents = []
    
    if os.path.exists(docs_dir):
        # Define supported file extensions
        supported_extensions = [
            '.pdf',  # PDF files
            '.xlsx', '.xls',  # Excel files
            '.csv',  # CSV files
        ]
        
        for filename in os.listdir(docs_dir):
            file_path = os.path.join(docs_dir, filename)
            if os.path.isfile(file_path):
                # Check if the file has a supported extension
                _, ext = os.path.splitext(filename.lower())
                if ext in supported_extensions:
                    documents.append(filename)
    
    return documents

def process_ocr_request(query, thread_id=None):
    """Process OCR request for PDF documents."""
    # Force output to be visible
    import sys
    sys.stdout.flush()
    print("\n\n=== CHECKING IF OCR REQUEST ===", flush=True)
    
    try:
        # Check if the query is asking for OCR
        ocr_pattern = re.compile(r'ocr|optical character recognition', re.IGNORECASE)
        
        # Print what we're looking for
        print(f"Query: '{query}'", flush=True)
        print(f"OCR pattern match: {bool(ocr_pattern.search(query))}", flush=True)
        
        # Simplified detection - just check for OCR keyword
        if not ocr_pattern.search(query):
            print("Not an OCR request - missing OCR keyword", flush=True)
            return None  # Not an OCR request
        
        print("=== OCR REQUEST DETECTED ===", flush=True)
        
        # Get the list of PDF documents
        documents = get_document_list()
        pdf_docs = [doc for doc in documents if doc.lower().endswith('.pdf')]
        
        if not pdf_docs:
            print("No PDF documents found", flush=True)
            return {
                "response": "No PDF documents found. Please upload a PDF document first.",
                "thread_id": thread_id,
                "success": False
            }
        
        print(f"Found PDF documents: {pdf_docs}", flush=True)
        
        try:
            # Check if MISTRAL_API_KEY is set in the environment
            mistral_api_key = os.environ.get("MISTRAL_API_KEY")
            if not mistral_api_key:
                print("MISTRAL_API_KEY not found in environment variables", flush=True)
                return {
                    "response": "OCR processing requires a Mistral API key. Please add MISTRAL_API_KEY to your .env file.",
                    "thread_id": thread_id,
                    "success": False
                }
            
            print(f"MISTRAL_API_KEY found: {mistral_api_key[:5]}...{mistral_api_key[-5:]}", flush=True)
            
            # Import Mistral client
            try:
                from mistralai import Mistral
            except ImportError:
                return {
                    "response": "OCR processing requires the Mistral AI package. Please install it with 'pip install mistralai'.",
                    "thread_id": thread_id,
                    "success": False
                }
            
            # For simplicity, use the first PDF in the list
            docs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
            pdf_path = os.path.join(docs_directory, pdf_docs[0])
            
            print(f"Processing PDF for OCR: {pdf_path}")
            
            # Initialize Mistral client
            client = Mistral(api_key=mistral_api_key)
            
            # Upload the PDF file for OCR
            try:
                print(f"Uploading PDF for OCR: {pdf_path}")
                
                uploaded_pdf = client.files.upload(
                    file={
                        "file_name": pdf_docs[0],
                        "content": open(pdf_path, "rb"),
                    },
                    purpose="ocr"
                )
                
                print(f"File uploaded successfully with ID: {uploaded_pdf.id}")
                
                # Get signed URL for the uploaded file
                signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
                print(f"Got signed URL: {signed_url.url}")
                
                # Process the uploaded file with OCR using the signed URL
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": signed_url.url,
                    }
                )
                
                # Extract text from response
                if hasattr(ocr_response, 'pages') and ocr_response.pages:
                    # Combine text from all pages
                    ocr_text = ""
                    for page in ocr_response.pages:
                        if hasattr(page, 'text'):
                            ocr_text += page.text + "\n\n"
                        else:
                            ocr_text += str(page) + "\n\n"
                else:
                    ocr_text = str(ocr_response)
                
                # Format as markdown
                markdown_text = f"# OCR Results for {pdf_docs[0]}\n\n"
                markdown_text += "```\n"
                markdown_text += ocr_text
                markdown_text += "\n```"
                
                return {
                    "response": markdown_text,
                    "thread_id": thread_id,
                    "success": True
                }
                
            except Exception as e:
                print(f"Error in Mistral OCR processing: {str(e)}")
                
                # Fall back to basic text extraction
                import pypdf
                
                reader = pypdf.PdfReader(pdf_path)
                text = ""
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                if not text.strip():
                    return {
                        "response": f"The PDF document {pdf_docs[0]} doesn't contain extractable text, and Mistral OCR failed with error: {str(e)}",
                        "thread_id": thread_id,
                        "success": False
                    }
                
                return {
                    "response": f"Mistral OCR failed, but basic text extraction from {pdf_docs[0]} succeeded:\n\n{text[:1500]}...",
                    "thread_id": thread_id,
                    "success": True
                }
                
        except Exception as e:
            print(f"Error in OCR processing: {str(e)}")
            return {
                "response": f"Error during OCR processing: {str(e)}",
                "thread_id": thread_id,
                "success": False
            }
    except Exception as e:
        print(f"Error in process_ocr_request: {str(e)}")
        return {
            "response": f"Error processing OCR request: {str(e)}",
            "thread_id": thread_id,
            "success": False
        }
