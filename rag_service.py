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
    """Split documents with extremely fine-grained chunking for better retrieval."""
    if not documents:
        print("No documents to split")
        return []
    
    docs_by_type = {
        'pdf': [],
        'excel': [],
        'csv': []
    }
    
    for doc in documents:
        file_type = doc.metadata.get('file_type', 'pdf')  
        if file_type in docs_by_type:
            docs_by_type[file_type].append(doc)
        else:
            docs_by_type['pdf'].append(doc) 
    
    all_chunks = []
    
    if docs_by_type['pdf']:
        # Use very small chunks with significant overlap for PDFs
        pdf_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Very small chunks
            chunk_overlap=250,  # 50% overlap
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        pdf_chunks = pdf_splitter.split_documents(docs_by_type['pdf'])
        print(f"Split {len(docs_by_type['pdf'])} PDF documents into {len(pdf_chunks)} chunks")
        all_chunks.extend(pdf_chunks)
    
    for doc_type in ['excel', 'csv']:
        if docs_by_type[doc_type]:
            table_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,  # Smaller chunks for tabular data
                chunk_overlap=200,
                length_function=len,
                separators=["\n", ",", "\t", " ", ""]
            )
            table_chunks = table_splitter.split_documents(docs_by_type[doc_type])
            print(f"Split {len(docs_by_type[doc_type])} {doc_type} documents into {len(table_chunks)} chunks")
            all_chunks.extend(table_chunks)
    
    print(f"Total chunks created: {len(all_chunks)}")
    return all_chunks

def initialize_system():
    """Initialize the RAG system with completely overhauled retrieval and prompting."""
    global _llm, _embeddings, _vector_store, _chain, _is_initialized, _memory
    
    if _is_initialized:
        return _chain
    
    print("Initializing RAG system with advanced retrieval...")
    
    # Use GPT-4o with strict factual settings
    _llm = ChatOpenAI(model="gpt-4o", temperature=0)
    print("LLM initialized")
    
    # Use the latest embedding model with maximum dimensions
    _embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=3072)
    print("Embeddings initialized")
    
    # Create vector store
    _vector_store = InMemoryVectorStore(embedding=_embeddings)
    print("Vector store initialized")
    
    # Load all documents
    all_documents = load_documents()
    
    # Process documents with improved chunking
    if all_documents:
        text_chunks = split_documents(all_documents)
        if text_chunks:
            print(f"Adding {len(text_chunks)} text chunks to vector store...")
            _vector_store.add_documents(documents=text_chunks)
            print(f"Documents added to vector store.")
    else:
        print("WARNING: No documents were loaded")
    
    # Create a hybrid retriever that combines semantic search with keyword search
    def hybrid_retrieval(query, top_k=10):
        """Hybrid retrieval combining semantic and keyword search."""
        # Semantic search
        semantic_docs = _vector_store.similarity_search(query, k=top_k)
        
        # Simple keyword search (as a backup)
        query_terms = set(query.lower().split())
        all_docs = load_documents()
        
        # Score documents by keyword matches
        keyword_scores = []
        for doc in all_docs:
            content = doc.page_content.lower()
            # Count how many query terms appear in the document
            matches = sum(1 for term in query_terms if term in content)
            if matches > 0:
                keyword_scores.append((doc, matches))
        
        # Sort by number of matches (descending)
        keyword_docs = [doc for doc, _ in sorted(keyword_scores, key=lambda x: x[1], reverse=True)[:top_k]]
        
        # Combine results (semantic first, then keyword)
        combined_docs = []
        seen_contents = set()
        
        # Add semantic results first
        for doc in semantic_docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_contents:
                combined_docs.append(doc)
                seen_contents.add(content_hash)
        
        # Add keyword results that aren't duplicates
        for doc in keyword_docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_contents and len(combined_docs) < top_k:
                combined_docs.append(doc)
                seen_contents.add(content_hash)
        
        return combined_docs[:top_k]
    
    def format_docs(docs):
        """Format documents with clear source attribution and page numbers."""
        if not docs:
            return "No relevant information found in the documents."
        
        formatted_text = ""
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown source')
            file_type = doc.metadata.get('file_type', 'document')
            page_num = doc.metadata.get('page', '')
            page_info = f" (page {page_num})" if page_num else ""
            
            # Add clear section header
            formatted_text += f"\n\n### DOCUMENT SECTION {i+1} ###\n"
            formatted_text += f"Source: {source}{page_info}, Type: {file_type}\n"
            formatted_text += f"Content:\n{doc.page_content}\n"
            formatted_text += f"### END OF DOCUMENT SECTION {i+1} ###"
        
        return formatted_text
    
    # Define the nodes for our graph
    def retrieve_context(state):
        """Retrieve relevant documents using hybrid retrieval."""
        # Get the last user message
        messages = state.get("messages", [])
        if not messages or messages[-1].get("role") != "user":
            return state
        
        query = messages[-1].get("content", "")
        
        # Create an enhanced query that includes context from conversation
        enhanced_query = query
        
        # If we have conversation history, use it to enhance the query
        if len(messages) > 2:
            # Get the last exchange
            last_user_msg = ""
            last_assistant_msg = ""
            
            for msg in messages[-3:-1]:
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content", "")
                elif msg.get("role") == "assistant":
                    last_assistant_msg = msg.get("content", "")
            
            if last_user_msg and last_assistant_msg:
                enhanced_query = f"Previous question: {last_user_msg}\nPrevious answer: {last_assistant_msg}\nNew question: {query}"
        
        print(f"Enhanced query: {enhanced_query}")
        
        # Use hybrid retrieval
        docs = hybrid_retrieval(enhanced_query, top_k=12)
        formatted_docs = format_docs(docs)
        
        # Add the context to the state
        state["context"] = formatted_docs
        state["raw_docs"] = docs  # Store raw docs for potential follow-up
        return state
    
    def generate_response(state):
        """Generate a response with strict adherence to document content."""
        # Get the last user message
        messages = state.get("messages", [])
        if not messages or messages[-1].get("role") != "user":
            return state
        
        query = messages[-1].get("content", "")
        
        # Format conversation history for context
        chat_context = ""
        for msg in messages[:-1]:  # Exclude the current message
            role = "User" if msg.get("role") == "user" else "Assistant"
            chat_context += f"{role}: {msg.get('content', '')}\n\n"
        
        # Check if we have relevant documents
        if "context" in state and state["context"] and "No relevant information" not in state["context"]:
            # Completely overhauled prompt with strict instructions
            prompt = f"""You are a document analysis AI with STRICT instructions to ONLY use information from the provided document sections.

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:
1. ONLY answer using information explicitly stated in the document sections below.
2. If the answer is not in the documents, say "I cannot find information about this in the provided documents."
3. NEVER make up information or use your general knowledge.
4. ALWAYS cite your sources by referring to specific document sections (e.g., "According to Document Section 2...").
5. Be precise and factual - accuracy is your top priority.
6. For data from Excel or CSV files, present it in a structured format.

Previous conversation:
{chat_context}

DOCUMENT SECTIONS:
{state["context"]}

User question:
{query}

Your answer (STRICTLY based ONLY on the document sections provided):"""
        else:
            # No relevant documents found
            prompt = f"""You are a document analysis AI.

I could not find any relevant information in the documents to answer this specific question.

Previous conversation:
{chat_context}

Question:
{query}

Your answer (inform the user that no relevant information was found):"""
        
        # Generate response with strict factuality
        response = _llm.invoke(prompt)
        
        # Add the assistant's response to the messages
        state["messages"].append({"role": "assistant", "content": response.content})
        return state
    
    # Build the graph
    builder = StateGraph(dict)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("generate_response", generate_response)
    
    # Add edges
    builder.add_edge("retrieve_context", "generate_response")
    builder.add_edge("generate_response", END)
    
    # Set the entry point
    builder.set_entry_point("retrieve_context")
    
    # Compile the graph with memory
    graph = builder.compile(checkpointer=_memory)
    
    def process_query(query, thread_id=None):
        """Process a query using the conversation graph."""
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Get existing conversation or create a new one
        config = {"configurable": {"thread_id": thread_id}}
        
        # Create the initial state as a dictionary
        state = {"messages": [{"role": "user", "content": query}]}
        
        # Run the graph
        try:
            result = graph.invoke(state, config=config)
            
            # Get the last message (the assistant's response)
            if result.get("messages") and len(result["messages"]) > 1:
                response = result["messages"][-1].get("content", "")
            else:
                response = "I'm sorry, I couldn't process your query properly."
            
            return response
        except Exception as e:
            print(f"Error in graph execution: {str(e)}")
            return f"Error processing your query: {str(e)}"
    
    _chain = process_query
    
    _is_initialized = True
    print("RAG system initialization complete with advanced retrieval")
    return _chain

def process_query(query, thread_id=None):
    """Process a user query and return the response with improved error handling."""
    if not _is_initialized:
        initialize_system()
    
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
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
                "response": "I don't have any documents in my knowledge base yet, but I can still try to answer your question based on my general knowledge. What would you like to know?",
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
        
        print(f"Processing query: '{query}'")
        # Run the chain with thread_id for memory
        response = _chain(query, thread_id)
        
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
