from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import logging
from dotenv import load_dotenv
from src.pdf_processor import load_pdf, create_vectorstore
from src.chat_handler import setup_chat, process_message
import uuid
import threading

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'src/files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory storage for chains (not serializable in sessions)
user_chains = {}

def get_session_id():
    """Get or create session ID."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def initialize_session():
    """Initialize session variables."""
    session_id = get_session_id()
    if 'messages' not in session:
        session['messages'] = []
    if 'pdf_uploaded' not in session:
        session['pdf_uploaded'] = False
    
    # Initialize chains in memory storage
    if session_id not in user_chains:
        user_chains[session_id] = {
            'pdf_chain': None,
            'personal_chain': setup_chat(None, api_key)
        }

@app.route('/')
def index():
    initialize_session()
    return render_template('index.html')

def process_pdf_background(filepath, session_id, filename):
    """Process PDF in background thread."""
    try:
        docs = load_pdf(filepath)
        vectorstore = create_vectorstore(docs)
        user_chains[session_id]['pdf_chain'] = setup_chat(vectorstore, api_key)
        user_chains[session_id]['pdf_status'] = 'ready'
        logger.info(f"PDF {filename} processed successfully")
    except Exception as e:
        user_chains[session_id]['pdf_status'] = 'error'
        user_chains[session_id]['pdf_error'] = str(e)
        logger.error(f"Error processing PDF {filename}: {str(e)}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and file.filename.lower().endswith('.pdf'):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{get_session_id()}.pdf')
            file.save(filepath)
            
            session_id = get_session_id()
            session['pdf_uploaded'] = True
            session['pdf_filename'] = file.filename
            
            # Set processing status
            user_chains[session_id]['pdf_status'] = 'processing'
            
            # Start background processing
            thread = threading.Thread(target=process_pdf_background, args=(filepath, session_id, file.filename))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True, 
                'message': 'PDF uploaded! Processing in background...',
                'filename': file.filename
            })
        except Exception as e:
            logger.error(f"Error uploading PDF: {str(e)}")
            return jsonify({'success': False, 'message': f'Error uploading PDF: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Please upload a valid PDF file'})

@app.route('/pdf_status', methods=['GET'])
def pdf_status():
    session_id = get_session_id()
    chains = user_chains.get(session_id, {})
    status = chains.get('pdf_status', 'none')
    
    if status == 'error':
        return jsonify({
            'status': 'error',
            'message': chains.get('pdf_error', 'Unknown error')
        })
    
    return jsonify({'status': status})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'success': False, 'message': 'Empty message'})
    
    try:
        # Add user message to session
        session['messages'].append({"role": "user", "content": user_message})
        
        # Get chains from memory storage
        session_id = get_session_id()
        chains = user_chains.get(session_id, {})
        
        # Check if PDF is ready
        pdf_status = chains.get('pdf_status', 'none')
        if pdf_status == 'processing':
            return jsonify({'success': False, 'message': 'PDF is still processing. Please wait...'})
        
        # Determine if question is PDF-related
        pdf_related = False
        if session.get('pdf_uploaded') and chains.get('pdf_chain') and pdf_status == 'ready':
            pdf_keywords = ['pdf', 'document', 'text', 'file', 'content', 'page', 'section']
            pdf_related = any(keyword in user_message.lower() for keyword in pdf_keywords)
        
        # Get response from appropriate chain
        if pdf_related:
            response = process_message(chains['pdf_chain'], user_message, session.get('messages', []))
        else:
            response = process_message(chains['personal_chain'], user_message, session.get('messages', []))
        
        # Add assistant response to session
        session['messages'].append({"role": "assistant", "content": response})
        
        return jsonify({
            'success': True, 
            'response': response,
            'messages': session['messages']
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/clear', methods=['POST'])
def clear_chat():
    session['messages'] = []
    return jsonify({'success': True, 'message': 'Chat cleared'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)