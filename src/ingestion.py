import os
import io
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import sys

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import Config

# Initialize Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=Config.GOOGLE_API_KEY)

def extract_text_from_pdf(file_bytes):
    """
    Extracts raw text from a PDF file object.
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def get_vector_store(text_chunks):
    """
    Creates a FAISS vector store from text chunks.
    """
    if not text_chunks:
        return None
    
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    return vector_store

def process_document(file_bytes):
    """
    Orchestrates the whole process: Read -> Chunk -> Vectorize
    Returns: (raw_text, vector_store)
    """
    # 1. Get Raw Text
    raw_text = extract_text_from_pdf(file_bytes)
    
    if not raw_text:
        return None, None

    # 2. Split Text (Chunks)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200 
    )
    chunks = text_splitter.split_text(raw_text)

    # 3. Create Vector Store
    vector_store = get_vector_store(chunks)
    
    return raw_text, vector_store