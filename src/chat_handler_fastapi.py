from langchain_openai import ChatOpenAI
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from .prompts import CHAT_PROMPT
import logging

logger = logging.getLogger(__name__)

def setup_chat(vectorstore, api_key: str, messages=None):
    """Set up the chat system with memory and retriever."""
    messages = messages[-10:] if messages else []

    # Initialize language model
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4-1106-preview",
        temperature=0.7
    )
    
    if vectorstore:
        # Initialize memory for PDF chat
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True
        )
        
        # Add message history to PDF chat memory
        for msg in messages:
            if msg["role"] == "user":
                memory.chat_memory.add_user_message(msg["content"])
            else:
                memory.chat_memory.add_ai_message(msg["content"])
        
        # Configure retriever for PDF chat
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )
        
        # Create the QA chain
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
    else:
        # Create a simple conversation chain for personal chat
        memory = ConversationBufferMemory()
        
        # Add message history
        for msg in messages:
            if msg["role"] == "user":
                memory.chat_memory.add_user_message(msg["content"])
            else:
                memory.chat_memory.add_ai_message(msg["content"])
        
        qa_chain = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=True
        )
    return qa_chain

def format_chat_history(messages: list) -> str:
    """Format the chat history for the AI context."""
    chat_history = []
    for msg in messages[-10:]:
        if msg["role"] == "user":
            chat_history.append(f"Human: {msg['content']}")
        else:
            chat_history.append(f"Assistant: {msg['content']}")
    return "\n".join(chat_history)

def process_message(chain, user_input: str, messages=None):
    """Process a user message and return the AI response."""
    try:
        logger.debug(f'Processing message: {user_input}')
        
        messages = messages or []
        
        # Format chat history for context
        chat_history = format_chat_history(messages)
        logger.debug(f'Chat history: {chat_history}')

        # Check if this is a PDF chain or personal chat
        is_pdf_chain = hasattr(chain, 'retriever')
        
        # Process the input through the chain
        if is_pdf_chain:
            response = chain.invoke({
                "question": user_input,
                "chat_history": chat_history
            })
            return response["answer"]
        else:
            response = chain.invoke({
                "input": user_input
            })
            return response["response"]

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return "I apologize, but I encountered an error. Please try again."