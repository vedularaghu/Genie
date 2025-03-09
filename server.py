from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import rag_service

app = Flask(__name__)
# Enable CORS for React frontend
CORS(app, supports_credentials=True)

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max upload size
app.secret_key = 'genie_secret_key'  # Add a secret key for session management

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/api/init', methods=['GET'])
def init():
    documents = rag_service.get_document_list()
    return jsonify({'documents': documents})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('message', '')
    
    # Process the query without thread_id
    result = rag_service.process_query(query)
    
    return jsonify(result)

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    # Clear chat history without thread_id
    rag_service.clear_chat_history()  # Assuming you have a function to clear chat history
    return jsonify({'success': True, 'message': 'Chat history cleared'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    # Define supported file extensions (removed image types)
    supported_extensions = [
        '.pdf',  # PDF files
        '.xlsx', '.xls',  # Excel files
        '.csv',  # CSV files
    ]
    
    # Check if the file has a supported extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext in supported_extensions:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(file_path)
        
        # Reinitialize the RAG system to include the new document
        rag_service._is_initialized = False
        rag_service.initialize_system()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully uploaded {filename}',
        })
    else:
        return jsonify({
            'success': False, 
            'message': 'Unsupported file type. Please upload PDF, Excel, or CSV files.'
        })

@app.route('/api/documents', methods=['GET'])
def get_documents():
    documents = rag_service.get_document_list()
    return jsonify({'documents': documents})

@app.route('/api/documents/delete', methods=['POST'])
def delete_document():
    data = request.json
    document_name = data.get('document', '')
    
    if not document_name:
        return jsonify({'success': False, 'message': 'No document specified'})
    
    try:
        # Get the full path to the document
        document_path = os.path.join(app.config['UPLOAD_FOLDER'], document_name)
        
        # Check if the file exists
        if not os.path.exists(document_path):
            return jsonify({'success': False, 'message': 'Document not found'})
        
        # Delete the file
        os.remove(document_path)
        
        # Reinitialize the RAG system to reflect the changes
        rag_service._is_initialized = False
        
        return jsonify({
            'success': True, 
            'message': f'Successfully deleted {document_name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/reset', methods=['POST'])
def reset_system():
    try:
        rag_service._is_initialized = False
        rag_service.initialize_system()
        return jsonify({'success': True, 'message': 'System reset successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Serve React app in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # This will serve the React app in production
    # For development, React will be served by the React development server
    if app.debug:
        return jsonify({"message": "API server is running. React app should be started separately in development mode."})
    
    # In production, serve the built React app
    from flask import send_from_directory
    if path != "" and os.path.exists(os.path.join('frontend/build', path)):
        return send_from_directory('frontend/build', path)
    else:
        return send_from_directory('frontend/build', 'index.html')

if __name__ == '__main__':
    # Initialize the RAG system on startup
    rag_service.initialize_system()
    app.run(debug=True, host='0.0.0.0', port=8080)
