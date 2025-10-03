from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import PyPDF2
import requests
import uuid
import io
from typing import Dict

app = FastAPI()

# In-memory storage
user_sessions: Dict[str, Dict] = {}

@app.get("/pdf_status")
async def pdf_status():
    return JSONResponse({"status": "ready"})

@app.post("/clear")
async def clear_chat(request: Request):
    session_id = request.cookies.get("session_id", "default")
    if session_id in user_sessions:
        user_sessions[session_id]['messages'] = []
    return JSONResponse({"success": True, "message": "Chat cleared"})

class ChatMessage(BaseModel):
    message: str

def extract_pdf_text(file_content):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def chat_openai(message, pdf_text=None, chat_history=None):
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        
        messages = [{"role": "system", "content": "You are a helpful AI assistant. Remember and use personal information shared by users in our conversation. When users tell you their name, age, or other personal details, remember them for future reference. Always maintain conversation context and refer back to previously shared information when relevant."}]
        if pdf_text:
            messages.append({"role": "system", "content": f"PDF: {pdf_text[:2000]}"})
        
        # Add chat history for memory - include more messages for better context
        if chat_history:
            messages.extend(chat_history[-20:])  # Last 20 messages for better memory
        
        messages.append({"role": "user", "content": message})
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

def get_session_id(request: Request) -> str:
    return request.cookies.get("session_id", str(uuid.uuid4()))

@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html", "r") as f:
        html_content = f.read()
    return html_content

@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = extract_pdf_text(content)
        
        # Store in session
        session_id = request.cookies.get("session_id", "default")
        if session_id not in user_sessions:
            user_sessions[session_id] = {}
        
        user_sessions[session_id]['pdf_text'] = text
        user_sessions[session_id]['pdf_filename'] = file.filename
        
        return JSONResponse({
            "success": True,
            "message": "PDF processed successfully!",
            "filename": file.filename
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        message = data.get('message', '').strip()
        
        if not message:
            return JSONResponse({"success": False, "message": "Empty message"}, status_code=400)
        
        # Get session data
        session_id = request.cookies.get("session_id", "default")
        if session_id not in user_sessions:
            user_sessions[session_id] = {'messages': [], 'pdf_text': None}
        
        session_data = user_sessions[session_id]
        pdf_text = session_data.get('pdf_text')
        chat_history = session_data.get('messages', [])
        
        # Add user message to history
        session_data['messages'].append({"role": "user", "content": message})
        
        response = chat_openai(message, pdf_text, chat_history)
        
        # Add assistant response to history
        session_data['messages'].append({"role": "assistant", "content": response})
        
        return JSONResponse({
            "success": True,
            "response": response
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)