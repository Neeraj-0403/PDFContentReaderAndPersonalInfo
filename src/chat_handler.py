from langchain_openai import ChatOpenAI
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from .prompts import CHAT_PROMPT
import streamlit as st

def setup_chat(vectorstore, api_key: str):
    """Set up the chat system with memory and retriever."""
    # Initialize the conversation buffer in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize the memory with conversation history
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True,
        input_key="question"
    )
    
    # Convert stored messages to memory format
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            memory.chat_memory.add_user_message(msg["content"])
        else:
            memory.chat_memory.add_ai_message(msg["content"])

    # Configure retriever
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}  # Retrieve top 3 most relevant chunks
    )
    
    # Initialize language model
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4-1106-preview",
        temperature=0.7
    )

    # Create the QA chain with combined document context and chat history
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        output_key="answer",
        return_source_documents=True,
        combine_docs_chain_kwargs={
            "prompt": CHAT_PROMPT,
        }
    )  
    return qa_chain

def format_chat_history(messages: list) -> str:
    """Format the chat history for the AI context."""
    chat_history = []
    for msg in messages[-10:]:  # Last 10 messages for context
        if msg["role"] == "user":
            chat_history.append(f"Human: {msg['content']}")
        else:
            chat_history.append(f"Assistant: {msg['content']}")
    return "\n".join(chat_history)

def process_message(chain, user_input: str):
    """Process a user message and return the AI response."""
    try:
        # Initialize messages if not exists
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Format chat history for context
        chat_history = format_chat_history(st.session_state.messages)

        # Process the input through the chain
        response = chain.invoke({
            "question": user_input,
            "chat_history": chat_history
        })
        
        # Extract the answer from the response
        answer = response["answer"] if isinstance(response, dict) else str(response)

        return answer

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return "I apologize, but I encountered an error. Please try again."
