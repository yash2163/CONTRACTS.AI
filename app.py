import streamlit as st
from src.database import SessionLocal, Session, Contract, ChatMessage, update_session_name, save_session_reports, get_session_details
from src.ingestion import process_document, get_vector_store
from src.rag_engine import analyze_contract_overview, check_risks_and_compliance, chat_response
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

# Sidebar: Session List
st.sidebar.title("🗂️ Contract History")

if st.sidebar.button("+ New Analysis"):
    st.session_state["current_session_id"] = create_new_session()
    st.rerun()

# Load Sessions
db = get_db_session()
sessions = db.query(Session).order_by(Session.created_at.desc()).all()
db.close()

session_ids = [s.id for s in sessions]

# Handle Session State
if "current_session_id" not in st.session_state:
    if sessions:
        st.session_state["current_session_id"] = sessions[0].id
    else:
        st.session_state["current_session_id"] = create_new_session()
        st.rerun()
elif st.session_state["current_session_id"] not in session_ids:
    if sessions:
        st.session_state["current_session_id"] = sessions[0].id
    else:
        st.session_state["current_session_id"] = create_new_session()
        st.rerun()

# Sidebar: Select Session
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

if selected_session_id != st.session_state["current_session_id"]:
    st.session_state["current_session_id"] = selected_session_id
    st.rerun()

current_session_id = st.session_state["current_session_id"]

# Sidebar: Rename Feature
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Session Settings")
current_session_obj = get_session_details(current_session_id)
new_name = st.sidebar.text_input("Rename Session", value=current_session_obj.name)
if st.sidebar.button("Update Name"):
    update_session_name(current_session_id, new_name)
    st.success("Updated!")
    st.rerun()

# --- MAIN CONTENT ---
st.title("⚖️ CONTRACTS.AI")

# Check for Contract
contract_text = get_session_contract_text(current_session_id)
vector_store = None

if contract_text:
    # Hydrate Vector Store
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = text_splitter.split_text(contract_text)
    vector_store = get_vector_store(chunks)
    st.success(f"✅ Contract Loaded: {current_session_obj.name}")
else:
    st.info("Start by uploading a contract.")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_file:
        with st.spinner("Processing..."):
            raw_text, vs = process_document(uploaded_file.read())
            if raw_text:
                save_contract_text(current_session_id, uploaded_file.name, raw_text)
                # Auto-rename session to filename for convenience
                update_session_name(current_session_id, uploaded_file.name)
                st.rerun()

# --- TABS ---
if vector_store:
    tab1, tab2, tab3 = st.tabs(["📄 Overview", "🚨 Risk & Compliance", "💬 Chat Assistant"])

    # Load fresh details from DB
    session_data = get_session_details(current_session_id)

    with tab1:
        st.subheader("Contract Summary")
        # Check if we already have it saved
        if session_data.overview_report:
            st.markdown(session_data.overview_report)
            if st.button("Re-Generate Overview"):
                 with st.spinner("Analyzing..."):
                    overview = analyze_contract_overview(vector_store)
                    save_session_reports(current_session_id, overview=overview)
                    st.rerun()
        else:
            if st.button("Generate Overview"):
                with st.spinner("Analyzing..."):
                    overview = analyze_contract_overview(vector_store)
                    save_session_reports(current_session_id, overview=overview)
                    st.rerun()

    with tab2:
        st.subheader("Risk Analysis Report")
        if session_data.risk_report:
            st.markdown(session_data.risk_report)
            if st.button("Re-Scan Risks"):
                 with st.spinner("Auditing..."):
                    risks = check_risks_and_compliance(vector_store)
                    save_session_reports(current_session_id, risks=risks)
                    st.rerun()
        else:
            if st.button("Scan for Risks"):
                with st.spinner("Auditing..."):
                    risks = check_risks_and_compliance(vector_store)
                    save_session_reports(current_session_id, risks=risks)
                    st.rerun()

    with tab3:
        st.subheader("Chat with your Contract")
        history = load_session_history(current_session_id)
        for msg in history:
            with st.chat_message(msg.role):
                st.write(msg.content)

        user_query = st.chat_input("Ask a question...")
        if user_query:
            with st.chat_message("user"):
                st.write(user_query)
            save_chat_message(current_session_id, "user", user_query)

            with st.spinner("Thinking..."):
                response = chat_response(user_query, vector_store)
                with st.chat_message("assistant"):
                    st.write(response)
                save_chat_message(current_session_id, "assistant", response)