import streamlit as st
from dotenv import load_dotenv
import os
from src.pdf_processor import load_pdf, create_vectorstore
from src.chat_handler import setup_chat, process_message

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# -------------------
# Streamlit UI Setup
# -------------------
st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.title("📘 PDF + Personal Chatbot")

#uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chain" not in st.session_state:
        st.session_state.chain = None

def main():
    # Initialize session state
    initialize_session_state()

    # File uploader with unique key
    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key="pdf_uploader"
    )

    if uploaded_file:
        # Process PDF
        with open("src/files/temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        
        # Only create new chain if not already exists or new file uploaded
        file_hash = hash(uploaded_file.getvalue())
        if "file_hash" not in st.session_state or st.session_state.file_hash != file_hash:
            st.session_state.file_hash = file_hash
            docs = load_pdf("src/files/temp.pdf")
            vectorstore = create_vectorstore(docs)
            st.session_state.chain = setup_chat(vectorstore, api_key)
            st.success("PDF processed successfully! You can now ask questions about it.")

        # Chat input with unique key
        user_input = st.chat_input(
            "Ask something...",
            key="chat_input"
        )

        if user_input:
            # Get AI response
            answer = process_message(st.session_state.chain, user_input)
            
            # Store the interaction
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": answer})

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

if __name__ == "__main__":
    main()
