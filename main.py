import streamlit as st
from dotenv import load_dotenv
import os
import logging
from src.pdf_processor import load_pdf, create_vectorstore
from src.chat_handler import setup_chat, process_message

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# -------------------
# Streamlit UI Setup
# -------------------
st.set_page_config(page_title="Personal Assistant & PDF Reader", layout="wide")
st.title("📘 Personal Assistant & PDF Reader")
st.write("Chat with me about anything! You can also upload a PDF to ask questions about it.")

def initialize_session_state():
    """Initialize session state variables."""
    logger.debug('Initializing session state')
    if "messages" not in st.session_state:
        logger.debug('Initializing messages list')
        st.session_state.messages = []
    if "pdf_chain" not in st.session_state:
        logger.debug('Initializing PDF chain')
        st.session_state.pdf_chain = None
    if "personal_chain" not in st.session_state:
        logger.debug('Initializing personal chat chain')
        st.session_state.personal_chain = setup_chat(None, api_key)  # Initialize personal chat
    if "processing" not in st.session_state:
        logger.debug('Initializing processing flag')
        st.session_state.processing = False
    
    # Debug current state
    logger.debug(f'Session state contents: {dict(st.session_state)}')

def main():
    # Initialize session state
    initialize_session_state()

    # Create a two-column layout
    col1, col2 = st.columns([2, 1])

    # Chat column (left)
    with col1:
        st.subheader("💬 Personal Chat")

        # Chat container for scrollable history
        chat_container = st.container()
        
        # Get user input first
        prompt = st.chat_input("How can I help you today?")
        
        # Display chat messages in the container
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            if prompt and not st.session_state.processing:
                # Set processing flag
                st.session_state.processing = True
                
                # Add user message to state and display it
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)
                
                # Create a placeholder for assistant's response
                with st.chat_message("assistant"):
                    # Determine if question is PDF-related
                    pdf_related = False
                    if st.session_state.pdf_chain is not None and "pdf_uploaded" in st.session_state:
                        pdf_keywords = ['pdf', 'document', 'text', 'file', 'content', 'page', 'section']
                        pdf_related = any(keyword in prompt.lower() for keyword in pdf_keywords)
                    
                # Get response from appropriate chain
                logger.debug(f'Processing prompt: {prompt}')
                logger.debug(f'PDF related: {pdf_related}')
                if pdf_related:
                    logger.debug('Using PDF chain')
                    response = process_message(st.session_state.pdf_chain, prompt)
                else:
                    logger.debug('Using personal chain')
                    response = process_message(st.session_state.personal_chain, prompt)
                    logger.debug(f'Got response: {response}')                    # Display the response
                    st.write(response)
                
                # Add assistant response to state
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Reset processing flag
                st.session_state.processing = False
                st.rerun()

    # PDF column (right)
    with col2:
        st.subheader("📄 PDF Upload & Questions")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload a PDF to ask questions",
            type=["pdf"],
            key="pdf_uploader"
        )

        if uploaded_file:
            # Create directory if it doesn't exist
            os.makedirs("src/files", exist_ok=True)
            
            # Process PDF
            with open("src/files/temp.pdf", "wb") as f:
                f.write(uploaded_file.read())
            
            # Only create new chain if new file uploaded
            file_hash = hash(uploaded_file.getvalue())
            if "file_hash" not in st.session_state or st.session_state.file_hash != file_hash:
                st.session_state.file_hash = file_hash
                docs = load_pdf("src/files/temp.pdf")
                vectorstore = create_vectorstore(docs)
                st.session_state.pdf_chain = setup_chat(vectorstore, api_key)
                st.session_state.pdf_uploaded = True
                st.success("✅ PDF processed successfully!")
                st.info("💡 You can now ask questions about the PDF content in the chat!")

if __name__ == "__main__":
    main()
