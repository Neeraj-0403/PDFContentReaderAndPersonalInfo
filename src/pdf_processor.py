from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def load_pdf(pdf_path: str):
    """Load and split PDF into chunks."""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load_and_split()
    return docs

def create_vectorstore(docs):
    """Create a vector store from document chunks."""
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore
