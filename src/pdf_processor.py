from langchain_community.document_loaders import PyPDFLoader, PDFMinerLoader, PyMuPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import logging

logger = logging.getLogger(__name__)

def load_pdf(pdf_path: str):
    """Load and split PDF into chunks using multiple loaders as fallbacks."""
    loaders = [
        ("PyPDFLoader", PyPDFLoader),
        ("PDFMinerLoader", PDFMinerLoader),
        ("PyMuPDFLoader", PyMuPDFLoader)
    ]
    
    for loader_name, loader_class in loaders:
        try:
            logger.info(f"Trying {loader_name}...")
            loader = loader_class(pdf_path)
            docs = loader.load_and_split()
            
            if docs:
                # Filter out empty documents
                docs = [doc for doc in docs if doc.page_content.strip()]
                
                if docs:
                    logger.info(f"Successfully loaded PDF with {loader_name}")
                    return docs
                    
        except Exception as e:
            logger.warning(f"{loader_name} failed: {str(e)}")
            continue
    
    raise Exception("Could not extract text from PDF. The file may be scanned images, password protected, or corrupted.")

def create_vectorstore(docs):
    """Create a vector store from document chunks."""
    try:
        if not docs:
            raise ValueError("No documents to create vectorstore")
            
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore
    except Exception as e:
        raise Exception(f"Failed to create vectorstore: {str(e)}")
