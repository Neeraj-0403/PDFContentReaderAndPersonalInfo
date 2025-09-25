// JavaScript for PDF Reader App

let isProcessing = false;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    focusMessageInput();
});

// Setup drag and drop functionality
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const fileInput = document.getElementById('fileInput');
            fileInput.files = files;
            uploadFile();
        }
    });
}

// Focus message input
function focusMessageInput() {
    document.getElementById('messageInput').focus();
}

// Handle Enter key press
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Send message function
async function sendMessage() {
    if (isProcessing) return;
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Clear input and disable send button
    messageInput.value = '';
    isProcessing = true;
    updateSendButton(true);
    
    // Add user message to chat
    addMessage('user', message);
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        hideTypingIndicator();
        
        if (data.success) {
            addMessage('assistant', data.response);
        } else {
            addMessage('assistant', 'Sorry, I encountered an error: ' + data.message);
        }
    } catch (error) {
        hideTypingIndicator();
        addMessage('assistant', 'Sorry, I encountered a connection error. Please try again.');
        console.error('Error:', error);
    } finally {
        isProcessing = false;
        updateSendButton(false);
        focusMessageInput();
    }
}

// Add message to chat
function addMessage(role, content) {
    const chatContainer = document.getElementById('chatContainer');
    const welcomeMessage = chatContainer.querySelector('.welcome-message');
    
    // Remove welcome message if it exists
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = content;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageDiv.appendChild(bubbleDiv);
    messageDiv.appendChild(timeDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const chatContainer = document.getElementById('chatContainer');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    typingDiv.appendChild(indicatorDiv);
    chatContainer.appendChild(typingDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Update send button state
function updateSendButton(disabled) {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    
    sendBtn.disabled = disabled;
    messageInput.disabled = disabled;
    
    if (disabled) {
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    }
}

// Upload file function
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showUploadStatus('Please select a PDF file.', 'error');
        return;
    }
    
    // Show loader
    showLoader(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showUploadStatus(data.message, 'success');
            showUploadedFile(data.filename);
            addMessage('assistant', '📄 PDF uploaded! Processing in background...');
            checkPdfStatus();
        } else {
            showUploadStatus(data.message, 'error');
        }
    } catch (error) {
        showUploadStatus('Upload failed. Please try again.', 'error');
        console.error('Upload error:', error);
    } finally {
        showLoader(false);
        fileInput.value = ''; // Clear file input
    }
}

// Show/hide loader
function showLoader(show) {
    const loaderContainer = document.getElementById('loaderContainer');
    if (show) {
        loaderContainer.classList.remove('d-none');
    } else {
        loaderContainer.classList.add('d-none');
    }
}

// Show upload status
function showUploadStatus(message, type) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = `<div class="status-${type}">${message}</div>`;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.innerHTML = '';
    }, 5000);
}

// Check PDF processing status
function checkPdfStatus() {
    const interval = setInterval(async () => {
        try {
            const response = await fetch('/pdf_status');
            const data = await response.json();
            
            if (data.status === 'ready') {
                clearInterval(interval);
                addMessage('assistant', '✅ PDF processed successfully! You can now ask questions about the PDF content.');
            } else if (data.status === 'error') {
                clearInterval(interval);
                addMessage('assistant', '❌ Error processing PDF: ' + data.message);
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }, 2000);
}

// Show uploaded file
function showUploadedFile(filename) {
    const uploadedFileDiv = document.getElementById('uploadedFile');
    const fileNameSpan = document.getElementById('fileName');
    
    fileNameSpan.textContent = filename;
    uploadedFileDiv.classList.remove('d-none');
}

// Clear chat function
async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        const response = await fetch('/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = `
                <div class="welcome-message text-center text-muted">
                    <i class="fas fa-robot fa-3x mb-3"></i>
                    <h5>Welcome! How can I help you today?</h5>
                    <p>You can chat with me about anything or upload a PDF to ask questions about it.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Clear chat error:', error);
    }
}