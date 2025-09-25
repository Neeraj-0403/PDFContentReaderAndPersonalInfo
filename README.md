# 📘 Personal Assistant & PDF Reader

A modern web application built with Flask, HTML, CSS, and Bootstrap that allows you to chat with an AI assistant and ask questions about uploaded PDF documents.

## ✨ Features

- **Personal Chat**: Chat with an AI assistant about anything
- **PDF Processing**: Upload PDF files and ask questions about their content
- **Modern UI**: Responsive design with Bootstrap and custom CSS
- **File Upload Loader**: Visual feedback during PDF processing
- **Real-time Chat**: Instant messaging with typing indicators
- **Drag & Drop**: Easy file upload with drag and drop support

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. **Clone or download the project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```
   
   Or directly:
   ```bash
   python app.py
   ```

5. **Open your browser** and go to: `http://localhost:5000`

## 🎯 Usage

### Personal Chat
- Type any message in the chat input
- The AI will respond to general questions and conversations
- Chat history is maintained during your session

### PDF Upload & Questions
1. **Upload a PDF**: 
   - Click "Choose File" or drag & drop a PDF file
   - Wait for the processing loader to complete
2. **Ask Questions**: 
   - Once processed, ask questions about the PDF content
   - The AI will use the PDF context to answer your questions

### Features
- **Clear Chat**: Use the "Clear Chat" button to reset conversation
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Feedback**: Loading indicators and status messages

## 🛠️ Technical Details

### Architecture
- **Backend**: Flask web framework
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **AI**: OpenAI GPT-4 with LangChain
- **PDF Processing**: PyPDF for text extraction
- **Vector Store**: FAISS for document similarity search

### File Structure
```
PdfContentReader/
├── app.py                 # Main Flask application
├── run.py                 # Application runner
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── src/
│   ├── chat_handler.py    # Chat logic and LangChain integration
│   ├── pdf_processor.py   # PDF processing and vectorization
│   ├── prompts.py         # AI prompt templates
│   └── files/             # Uploaded PDF storage
├── templates/
│   └── index.html         # Main HTML template
└── static/
    ├── css/
    │   └── style.css      # Custom styles
    └── js/
        └── app.js         # Frontend JavaScript
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Customization
- **Styling**: Modify `static/css/style.css` for custom appearance
- **Behavior**: Update `static/js/app.js` for frontend functionality
- **AI Prompts**: Edit `src/prompts.py` to customize AI responses

## 📱 Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## 🚨 Troubleshooting

### Common Issues

1. **"No module named 'flask'"**
   - Install dependencies: `pip install -r requirements.txt`

2. **"OpenAI API key not found"**
   - Create `.env` file with your API key
   - Ensure the key is valid and has credits

3. **PDF upload fails**
   - Check file size (max 16MB)
   - Ensure file is a valid PDF
   - Check server logs for detailed errors

4. **Chat not responding**
   - Verify internet connection
   - Check OpenAI API key and credits
   - Look at browser console for JavaScript errors

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.