import streamlit as st
import uuid
from src.database import SessionLocal, Session, Contract, ChatMessage
from src.ingestion import process_document, get_vector_store
from src.rag_engine import analyze_contract_overview, check_risks_and_compliance, chat_response
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Page Config
st.set_page_config(page_title="CONTRACTS.AI", layout="wide")

# --- DATABASE HELPERS ---
def get_db_session():
    return SessionLocal()

def create_new_session(name="New Contract Analysis"):
    db = get_db_session()
    new_session = Session(name=name)
    db.add(new_session)
    db.commit()
    session_id = new_session.id
    db.close()
    return session_id

def save_contract_text(session_id, filename, text):
    db = get_db_session()
    contract = Contract(session_id=session_id, filename=filename, content=text)
    db.add(contract)
    db.commit()
    db.close()

def load_session_history(session_id):
    db = get_db_session()
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()
    db.close()
    return messages

def save_chat_message(session_id, role, content):
    db = get_db_session()
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.close()

def get_session_contract_text(session_id):
    db = get_db_session()
    contract = db.query(Contract).filter(Contract.session_id == session_id).first()
    db.close()
    return contract.content if contract else None

# --- UI LOGIC ---

# Sidebar: Session Management
st.sidebar.title("🗂️ Contract History")

if st.sidebar.button("+ New Analysis"):
    st.session_state["current_session_id"] = create_new_session()
    st.rerun()

# 1. Load existing sessions from DB
db = get_db_session()
sessions = db.query(Session).order_by(Session.created_at.desc()).all()
db.close()

# 2. Collect all valid IDs
session_ids = [s.id for s in sessions]

# 3. Handle Initialization & Stale States
if "current_session_id" not in st.session_state:
    # Case A: No state yet.
    if sessions:
        st.session_state["current_session_id"] = sessions[0].id
    else:
        st.session_state["current_session_id"] = create_new_session()
        st.rerun() # Rerun to show the new session immediately

elif st.session_state["current_session_id"] not in session_ids:
    # Case B: State has an ID, but it's not in the DB (stale).
    if sessions:
        st.session_state["current_session_id"] = sessions[0].id
    else:
        st.session_state["current_session_id"] = create_new_session()
        st.rerun()

# 4. Render the Sidebar Radio
# Now we are 100% sure the ID in session_state exists in the list.
try:
    current_index = session_ids.index(st.session_state["current_session_id"])
except ValueError:
    current_index = 0

selected_session_id = st.sidebar.radio(
    "Select Session:",
    options=session_ids,
    format_func=lambda x: next((s.name for s in sessions if s.id == x), "Unknown"),
    index=current_index
)

# 5. Handle Selection Change
if selected_session_id != st.session_state["current_session_id"]:
    st.session_state["current_session_id"] = selected_session_id
    st.rerun()

current_session_id = st.session_state["current_session_id"]
# --- MAIN CONTENT ---
st.title("⚖️ CONTRACTS.AI")
st.markdown("### Intelligent Contract Lifecycle & Compliance Agent")

# Check if contract exists for this session
contract_text = get_session_contract_text(current_session_id)
vector_store = None

if contract_text:
    # Re-hydrate vector store from DB text (Fast for POC)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = text_splitter.split_text(contract_text)
    vector_store = get_vector_store(chunks)
    st.success("✅ Contract Loaded from Database")

else:
    uploaded_file = st.file_uploader("Upload a Contract (PDF)", type="pdf")
    if uploaded_file:
        with st.spinner("Processing Contract..."):
            raw_text, vs = process_document(uploaded_file.read())
            if raw_text:
                save_contract_text(current_session_id, uploaded_file.name, raw_text)
                vector_store = vs
                st.success("File Processed & Saved!")
                st.rerun()

# --- TABS FOR ANALYSIS ---
if vector_store:
    tab1, tab2, tab3 = st.tabs(["📄 Overview", "🚨 Risk & Compliance", "💬 Chat Assistant"])

    with tab1:
        st.subheader("Contract Summary")
        if st.button("Generate Overview"):
            with st.spinner("Analyzing..."):
                overview = analyze_contract_overview(vector_store)
                st.markdown(overview)

    with tab2:
        st.subheader("Risk Analysis Report")
        if st.button("Scan for Risks"):
            with st.spinner("Auditing Compliance..."):
                risks = check_risks_and_compliance(vector_store)
                st.markdown(risks)

    with tab3:
        st.subheader("Chat with your Contract")
        
        # Load history
        history = load_session_history(current_session_id)
        for msg in history:
            with st.chat_message(msg.role):
                st.write(msg.content)

        user_query = st.chat_input("Ask about penalties, dates, or clauses...")
        if user_query:
            # Display User Message
            with st.chat_message("user"):
                st.write(user_query)
            save_chat_message(current_session_id, "user", user_query)

            # Generate AI Response
            with st.spinner("Thinking..."):
                response = chat_response(user_query, vector_store)
                with st.chat_message("assistant"):
                    st.write(response)
                save_chat_message(current_session_id, "assistant", response)