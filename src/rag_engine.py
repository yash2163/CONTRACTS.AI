import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains.question_answering import load_qa_chain
from langchain_core.prompts import PromptTemplate

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import Config

# Initialize Gemini Model
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=Config.GOOGLE_API_KEY, temperature=0.3)

def get_conversational_chain():
    """
    Creates a chain for Q&A with specific contract-focused instructions.
    """
    prompt_template = """
    You are an expert Legal AI Assistant named 'Contracts.AI'.
    Your task is to analyze legal contracts with high precision.
    
    Context from the contract:
    {context}
    
    User Question:
    {question}
    
    Answer strictly based on the provided context. If the answer is not in the context, say "I cannot find this information in the document."
    Format your answer clearly using bullet points if necessary.
    """
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def analyze_contract_overview(vector_store):
    """
    Performs the initial automatic extraction of key data.
    """
    query = """
    Analyze this contract and extract the following details in a structured JSON-like format (but simple text):
    1. Contract Type (e.g., NDA, MSA, Lease)
    2. Parties Involved
    3. Effective Date & Expiration Date
    4. Key Obligations (Summarize top 3)
    5. Termination Conditions
    6. Financial Terms / Payment Clauses
    """
    
    # We perform a similarity search to get relevant chunks (or all if small)
    # For overview, we ideally want broad context.
    docs = vector_store.similarity_search(query, k=10)
    
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": query}, return_only_outputs=True)
    return response["output_text"]

def check_risks_and_compliance(vector_store):
    """
    Specific check for the 'Traffic Light' system and Risks.
    """
    query = """
    Identify critical risks and compliance gaps in this document.
    Focus on:
    - Unlimited Liability (High Risk)
    - Auto-renewal clauses (Medium Risk)
    - Non-standard payment terms (>60 days)
    - Missing Confidentiality clauses
    
    For each found issue, assign a Risk Level: [HIGH], [MEDIUM], or [LOW].
    """
    docs = vector_store.similarity_search(query, k=10)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": query}, return_only_outputs=True)
    return response["output_text"]

def chat_response(query, vector_store):
    """
    Handles user follow-up questions.
    """
    docs = vector_store.similarity_search(query, k=5)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": query}, return_only_outputs=True)
    return response["output_text"]