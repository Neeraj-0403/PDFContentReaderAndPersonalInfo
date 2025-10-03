from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
from src.pdf_processor import load_pdf, create_vectorstore
from src.chat_handler_fastapi import setup_chat, process_message
import uuid
import threading
from typing import Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="PDF Content Reader")

# Mount static files and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure upload directory exists
os.makedirs("src/files", exist_ok=True)

# In-memory storage
user_chains: Dict[str, Any] = {}
user_sessions: Dict[str, Dict] = {}

class ChatMessage(BaseModel):
    message: str

def get_session_id(request: Request) -> str:
    """Get or create session ID from cookies."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def initialize_session(session_id: str):
    """Initialize session variables."""
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            'messages': [],
            'pdf_uploaded': False,
            'pdf_filename': None
        }
    
    if session_id not in user_chains:
        user_chains[session_id] = {
            'pdf_chain': None,
            'personal_chain': setup_chat(None, api_key),
            'pdf_status': 'none'
        }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    session_id = get_session_id(request)
    initialize_session(session_id)
    
    response = templates.TemplateResponse("index.html", {"request": request})
    response.set_cookie("session_id", session_id)
    return response

def process_pdf_background(filepath: str, session_id: str, filename: str):
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

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    session_id = get_session_id(request)
    initialize_session(session_id)
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Please upload a valid PDF file")
    
    try:
        # Save file
        filepath = f"src/files/{session_id}.pdf"
        with open(filepath, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update session
        user_sessions[session_id]['pdf_uploaded'] = True
        user_sessions[session_id]['pdf_filename'] = file.filename
        user_chains[session_id]['pdf_status'] = 'processing'
        
        # Start background processing
        thread = threading.Thread(target=process_pdf_background, args=(filepath, session_id, file.filename))
        thread.daemon = True
        thread.start()
        
        return JSONResponse({
            "success": True,
            "message": "PDF uploaded! Processing in background...",
            "filename": file.filename
        })
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")

@app.get("/pdf_status")
async def pdf_status(request: Request):
    session_id = get_session_id(request)
    chains = user_chains.get(session_id, {})
    status = chains.get('pdf_status', 'none')
    
    if status == 'error':
        return JSONResponse({
            'status': 'error',
            'message': chains.get('pdf_error', 'Unknown error')
        })
    
    return JSONResponse({'status': status})

@app.post("/chat")
async def chat(request: Request, chat_data: ChatMessage):
    session_id = get_session_id(request)
    initialize_session(session_id)
    
    user_message = chat_data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")
    
    try:
        # Add user message to session
        user_sessions[session_id]['messages'].append({"role": "user", "content": user_message})
        
        # Get chains from memory storage
        chains = user_chains.get(session_id, {})
        
        # Check if PDF is ready
        pdf_status = chains.get('pdf_status', 'none')
        if pdf_status == 'processing':
            raise HTTPException(status_code=400, detail="PDF is still processing. Please wait...")
        
        # Determine if question is PDF-related
        pdf_related = False
        if user_sessions[session_id]['pdf_uploaded'] and chains.get('pdf_chain') and pdf_status == 'ready':
            pdf_keywords = ['pdf', 'document', 'text', 'file', 'content', 'page', 'section']
            pdf_related = any(keyword in user_message.lower() for keyword in pdf_keywords)
        
        # Get response from appropriate chain
        if pdf_related:
            response = process_message(chains['pdf_chain'], user_message, user_sessions[session_id]['messages'])
        else:
            response = process_message(chains['personal_chain'], user_message, user_sessions[session_id]['messages'])
        
        # Add assistant response to session
        user_sessions[session_id]['messages'].append({"role": "assistant", "content": response})
        
        return JSONResponse({
            "success": True,
            "response": response,
            "messages": user_sessions[session_id]['messages']
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/clear")
async def clear_chat(request: Request):
    session_id = get_session_id(request)
    if session_id in user_sessions:
        user_sessions[session_id]['messages'] = []
    return JSONResponse({"success": True, "message": "Chat cleared"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)