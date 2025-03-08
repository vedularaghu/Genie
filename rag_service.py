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
    """Split documents into chunks with improved settings for better context."""
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
        pdf_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        pdf_chunks = pdf_splitter.split_documents(docs_by_type['pdf'])
        print(f"Split {len(docs_by_type['pdf'])} PDF documents into {len(pdf_chunks)} chunks")
        all_chunks.extend(pdf_chunks)
    
    for doc_type in ['excel', 'csv']:
        if docs_by_type[doc_type]:
            table_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
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
    """Initialize the RAG system with improved retrieval and prompting."""
    global _llm, _embeddings, _vector_store, _chain, _is_initialized, _memory
    
    if _is_initialized:
        return _chain
    
    print("Initializing RAG system...")
    
    _llm = ChatOpenAI(model="gpt-4o", temperature=0)  
    print("LLM initialized")
    
    # Initialize embeddings
    _embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    print("Embeddings initialized")
    
    # Create vector store
    _vector_store = InMemoryVectorStore(embedding=_embeddings)
    print("Vector store initialized")
    
    # Load all documents
    all_documents = load_documents()
    
    # Process documents
    if all_documents:
        text_chunks = split_documents(all_documents)
        if text_chunks:
            print(f"Adding {len(text_chunks)} text chunks to vector store...")
            _vector_store.add_documents(documents=text_chunks)
            print(f"Documents added to vector store.")
    else:
        print("WARNING: No documents were loaded")
    
    # Create retriever
    retriever = _vector_store.as_retriever(
        search_kwargs={
            "k": 5,
            "score_threshold": 0.5
        }
    )
    
    def format_docs(docs):
        if not docs:
            return "No relevant information found in the documents."
        
        formatted_text = ""
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown source')
            file_type = doc.metadata.get('file_type', 'document')
            formatted_text += f"\n\nDocument {i+1} (from {source}, type: {file_type}):\n{doc.page_content}"
        
        return formatted_text
    
    # Define the nodes for our graph
    def retrieve_context(state):
        """Retrieve relevant documents for the query."""
        # Get the last user message
        messages = state.get("messages", [])
        if not messages or messages[-1].get("role") != "user":
            return state
        
        query = messages[-1].get("content", "")
        docs = retriever.invoke(query)
        formatted_docs = format_docs(docs)
        
        # Add the context to the state
        state["context"] = formatted_docs
        return state
    
    def generate_response(state):
        """Generate a response using the LLM."""
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
        if "context" in state and state["context"]:
            # Standard RAG prompt with chat history
            prompt = f"""You are an assistant for question-answering tasks. 
            Use the following pieces of retrieved context to answer the question. 
            If the answer is not fully contained in the context, you can also use your general knowledge to provide a complete answer.
            Always prioritize information from the documents when available.
            
            When using your general knowledge, clearly indicate which parts of your answer come from the documents and which parts come from your general knowledge.
            
            For data from Excel or CSV files, try to present it in a structured way if appropriate.

            Previous conversation:
            {chat_context}
            
            Context from documents:
            {state["context"]}

            Question:
            {query}

            Answer:"""
        else:
            # No relevant documents found
            prompt = f"""You are an assistant for question-answering tasks.
            I don't have specific document information about this query, so I'll answer based on my general knowledge.
            
            Previous conversation:
            {chat_context}
            
            Question:
            {query}
            
            Answer:"""
        
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
    print("RAG system initialization complete")
    return _chain

def process_query(query, thread_id=None):
    """Process a user query and return the response with improved error handling."""
    if not _is_initialized:
        initialize_system()
    
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    try:
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