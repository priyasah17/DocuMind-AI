import requests
import streamlit as st

# Streamlit page configuration must be the first Streamlit command.
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 180

# --------------------------------------------------
# MODERN UI STYLING
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --bg: #0b0d14;
        --panel: #121522;
        --border: #2a3042;
        --text: #f2f4fc;
        --muted: #9ba5bd;
        --accent: #8b5cf6;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 15% 0%, rgba(99,102,241,.13), transparent 32%),
            radial-gradient(ellipse at 90% 15%, rgba(139,92,246,.10), transparent 28%),
            var(--bg);
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stHeader"] { background: rgba(11,13,20,.82); }
    .block-container { max-width: 1320px; padding-top: 2rem; padding-bottom: 3rem; }

    [data-testid="stSidebar"] {
        background: #10131e;
        border-right: 1px solid var(--border);
    }

    h1, h2, h3 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -0.04em;
    }
    h1 { font-weight: 800 !important; }
    h2, h3 { font-weight: 700 !important; }
    p, label, [data-testid="stMarkdownContainer"] { color: #c7cce0; }
    [data-testid="stCaptionContainer"] { color: var(--muted) !important; }

    .hero {
        padding: 1.6rem 1.7rem;
        border: 1px solid #30334c;
        border-radius: 22px;
        background: linear-gradient(120deg, rgba(124,58,237,.18), rgba(99,102,241,.08) 52%, rgba(18,21,34,.92));
        margin-bottom: 1.3rem;
    }
    .hero-kicker {
        color: #b9a5ff;
        font-size: .78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .14em;
        margin-bottom: .5rem;
    }
    .hero-title {
        color: #fbfaff;
        font-family: 'Manrope', sans-serif;
        font-size: clamp(2rem, 4vw, 3.2rem);
        line-height: 1.1;
        font-weight: 800;
        letter-spacing: -.055em;
        margin: 0;
    }
    .hero-subtitle {
        color: #aeb6cd;
        font-size: 1rem;
        margin-top: .7rem;
        margin-bottom: 0;
        max-width: 720px;
    }
    .section-kicker {
        color: #a99aff;
        text-transform: uppercase;
        font-size: .73rem;
        font-weight: 700;
        letter-spacing: .13em;
        margin-bottom: .2rem;
    }
    .metric-card {
        border: 1px solid var(--border);
        background: linear-gradient(145deg, rgba(23,27,42,.96), rgba(16,19,30,.96));
        border-radius: 16px;
        padding: 1rem 1.1rem;
        min-height: 100px;
    }
    .metric-label { color: var(--muted); font-size: .84rem; }
    .metric-value {
        color: #f5f3ff;
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 1.8rem;
        margin-top: .2rem;
    }
    .stButton > button, .stDownloadButton > button {
        border: 1px solid #3a4058;
        border-radius: 11px;
        background: #1a1e2e;
        color: #f5f4ff;
        font-weight: 600;
        transition: all .18s ease;
        min-height: 2.65rem;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #9b87ff;
        background: #292440;
        color: white;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed, #6366f1);
        border: none;
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #6d28d9, #4f46e5);
    }
    .stTextInput input, .stTextArea textarea {
        background: #151928;
        color: #f5f6ff;
        border: 1px solid #343a50;
        border-radius: 10px;
    }
    [data-baseweb="select"] > div {
        background: #151928;
        border-color: #343a50;
        border-radius: 10px;
    }
    [data-testid="stFileUploader"] {
        background: rgba(19,23,37,.75);
        border: 1px dashed #62578d;
        border-radius: 15px;
        padding: .8rem;
    }
    [data-testid="stExpander"] {
        background: rgba(18,21,34,.85);
        border: 1px solid var(--border);
        border-radius: 12px;
    }
    [data-testid="stChatMessage"] {
        background: #141827;
        border: 1px solid #2a3042;
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: .7rem;
    }
    [data-testid="stChatInput"] {
        border: 1px solid #45405f;
        border-radius: 14px;
        background: #141827;
    }
    [data-testid="stAlert"] { border-radius: 12px; }
    hr { border-color: var(--border); margin: 1.4rem 0; }

    .footer {
        text-align: center;
        color: #737e99;
        font-size: .8rem;
        padding-top: 1rem;
    }
    @media (max-width: 768px) {
        .block-container { padding: 1rem .8rem 2rem; }
        .hero { padding: 1.2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_document_ids" not in st.session_state:
    st.session_state.selected_document_ids = []


# --------------------------------------------------
# API HELPER FUNCTIONS
# --------------------------------------------------
def get_documents():
    response = requests.get(f"{API_URL}/documents", timeout=10)
    response.raise_for_status()
    return response.json().get("documents", [])


def upload_pdfs(uploaded_files):
    files = [
        ("files", (pdf.name, pdf.getvalue(), "application/pdf"))
        for pdf in uploaded_files
    ]
    response = requests.post(
        f"{API_URL}/documents/upload",
        files=files,
        timeout=300,
    )
    response.raise_for_status()
    return response.json()


def delete_document(document_id):
    response = requests.delete(
        f"{API_URL}/documents/{document_id}",
        timeout=30,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def ask_documents(document_ids, question):
    response = requests.post(
        f"{API_URL}/documents/ask-multiple",
        json={
            "document_ids": document_ids,
            "query": question,
            "k": 3,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_source_filename(source):
    metadata = source.get("metadata") or {}
    return (
        source.get("filename")
        or source.get("file_name")
        or metadata.get("filename")
        or "Unknown PDF"
    )


def get_source_page(source):
    metadata = source.get("metadata") or {}
    return (
        source.get("page")
        or source.get("page_number")
        or metadata.get("page_number")
        or source.get("page_num")
    )


def get_source_content(source):
    return (
        source.get("content")
        or source.get("text")
        or source.get("page_content")
        or ""
    )


def display_sources(sources):
    if not sources:
        st.caption("No source passages were returned for this answer.")
        return

    with st.expander(
        f"📚 Sources used · {len(sources)} passage(s)",
        expanded=False,
    ):
        for index, source in enumerate(sources, start=1):
            filename = get_source_filename(source)
            page = get_source_page(source)
            content = get_source_content(source)

            st.markdown(f"**Source {index} · {filename}**")
            if page is not None:
                st.caption(f"Page {page}")
            if content:
                st.info(content)
            else:
                st.caption("No passage text was returned.")

            if index < len(sources):
                st.divider()


# --------------------------------------------------
# SIDEBAR: STATUS AND DOCUMENT LIBRARY
# --------------------------------------------------
with st.sidebar:
    st.markdown("## 📚 DocuMind AI")
    st.caption("Your personal document intelligence workspace")
    st.divider()

    st.markdown("### System status")
    if st.button("↻ Check backend", use_container_width=True):
        try:
            health = requests.get(f"{API_URL}/health", timeout=5)
            health.raise_for_status()
            st.success("Backend connected")
        except requests.RequestException:
            st.error("Backend unavailable. Start FastAPI on port 8000.")

    if st.button("🔄 Refresh documents", use_container_width=True):
        st.rerun()

    st.divider()
    st.markdown("### 📁 Your library")

    try:
        documents = get_documents()
        st.caption(f"{len(documents)} PDF(s) in your library")

        if not documents:
            st.info("Your library is empty. Upload a PDF to get started.")

        for document in documents:
            document_id = document.get("document_id", "")
            filename = document.get("filename", "Untitled PDF")
            status = document.get("status", "unknown")

            with st.expander(f"📄 {filename}"):
                st.caption(f"Status: {status}")
                st.caption("Document ID")
                st.code(document_id, language=None)

                confirm_key = f"confirm_delete_{document_id}"
                confirmed = st.checkbox(
                    "Confirm deletion",
                    key=confirm_key,
                )

                if st.button(
                    "Delete PDF",
                    key=f"delete_{document_id}",
                    use_container_width=True,
                ):
                    if not confirmed:
                        st.warning("Check Confirm deletion first.")
                    else:
                        try:
                            delete_document(document_id)
                            st.session_state.chat_history = [
                                message
                                for message in st.session_state.chat_history
                                if document_id not in message.get("document_ids", [])
                            ]
                            st.session_state.selected_document_ids = [
                                doc_id
                                for doc_id in st.session_state.selected_document_ids
                                if doc_id != document_id
                            ]
                            st.success(f"Deleted {filename}")
                            st.rerun()
                        except requests.RequestException as error:
                            st.error(f"Delete failed: {error}")

    except requests.RequestException:
        documents = []
        st.error("Cannot load the library. Check that FastAPI is running.")

    st.divider()
    if st.button("🧹 Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.caption("FastAPI · FAISS · Groq · OCR")


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">AI-powered knowledge workspace</div>
      <div class="hero-title">Ask your documents.<br>Find answers faster.</div>
      <p class="hero-subtitle">
        Upload PDFs, search across your knowledge base, and get AI-generated
        answers with source passages you can verify.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    current_documents = get_documents()
except requests.RequestException:
    current_documents = []

processed_count = sum(
    1 for document in current_documents
    if document.get("status") == "processed"
)

metric1, metric2, metric3 = st.columns(3)
with metric1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">PDFs in library</div>'
        f'<div class="metric-value">{len(current_documents)}</div></div>',
        unsafe_allow_html=True,
    )
with metric2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Ready to search</div>'
        f'<div class="metric-value">{processed_count}</div></div>',
        unsafe_allow_html=True,
    )
with metric3:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">AI assistant</div>'
        '<div class="metric-value" style="font-size:1.25rem">Ready when you are</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

# --------------------------------------------------
# UPLOAD DOCUMENTS
# --------------------------------------------------
st.markdown('<div class="section-kicker">STEP 1</div>', unsafe_allow_html=True)
st.header("📤 Add documents")
st.markdown(
    '<div class="muted">Choose one or more PDF files. DocuMind will extract text, '
    'split it into chunks, and prepare them for semantic search.</div>',
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Drop PDFs here or browse files",
    type=["pdf"],
    accept_multiple_files=True,
    key="pdf_uploader",
    help="You can select multiple PDFs at once.",
)

upload_col, upload_note_col = st.columns([1, 2], vertical_alignment="center")
with upload_col:
    if st.button(
        "✨ Process documents",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    ):
        try:
            with st.spinner("Extracting text and building search indexes..."):
                result = upload_pdfs(uploaded_files)

            processed = result.get("documents", [])
            st.success(f"Successfully processed {len(processed)} document(s).")

            for document in processed:
                st.write(
                    f"📄 **{document.get('filename', 'PDF')}** · "
                    f"{document.get('chunk_count', 0)} text chunks"
                )

            st.rerun()
        except requests.RequestException as error:
            st.error(f"Upload failed: {error}")
        except (KeyError, ValueError) as error:
            st.error(f"Unexpected backend response: {error}")

with upload_note_col:
    st.caption("Tip: Select several PDFs to ask questions across multiple documents.")

st.divider()

# --------------------------------------------------
# ASK YOUR DOCUMENTS
# --------------------------------------------------
st.markdown('<div class="section-kicker">STEP 2</div>', unsafe_allow_html=True)
st.header("💬 Chat with your knowledge base")
st.markdown(
    '<div class="muted">Choose the documents to search, then ask a question in natural language.</div>',
    unsafe_allow_html=True,
)

try:
    available_documents = get_documents()
    processed_documents = [
        document for document in available_documents
        if document.get("status") == "processed"
    ]

    if not processed_documents:
        st.info("Upload and process at least one PDF to start asking questions.")
    else:
        document_labels = {
            document["document_id"]: (
                f'{document.get("filename", "Untitled PDF")} '
                f'({document["document_id"][:8]})'
            )
            for document in processed_documents
        }

        valid_ids = set(document_labels)
        default_ids = [
            doc_id for doc_id in st.session_state.selected_document_ids
            if doc_id in valid_ids
        ]

        selected_ids = st.multiselect(
            "Search within",
            options=list(document_labels.keys()),
            default=default_ids,
            format_func=lambda doc_id: document_labels[doc_id],
            help="Select one or more PDFs. Select multiple to search across them.",
        )
        st.session_state.selected_document_ids = selected_ids

        if selected_ids:
            st.caption(f"{len(selected_ids)} document(s) selected for this conversation.")
        else:
            st.caption("Select at least one PDF before asking a question.")

        # Display saved conversation history.
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    display_sources(message.get("sources", []))

        question = st.chat_input("Ask a question about your selected PDFs…")
        if question:
            if not selected_ids:
                st.warning("Select at least one PDF before asking a question.")
            else:
                st.session_state.chat_history.append(
                    {
                        "role": "user",
                        "content": question,
                        "document_ids": list(selected_ids),
                    }
                )
                with st.chat_message("user"):
                    st.markdown(question)

                try:
                    with st.spinner("Searching your PDFs and preparing an answer..."):
                        result = ask_documents(selected_ids, question)

                    answer = result.get("answer", "No answer was returned.")
                    sources = result.get("sources", [])

                    assistant_message = {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "document_ids": list(selected_ids),
                    }
                    st.session_state.chat_history.append(assistant_message)

                    with st.chat_message("assistant"):
                        st.markdown(answer)
                        display_sources(sources)

                except requests.RequestException as error:
                    st.error(f"Question failed: {error}")

except requests.RequestException as error:
    st.error(f"Could not connect to the backend: {error}")

st.divider()
st.markdown(
    '<div class="footer">DocuMind AI · Built with FastAPI, Streamlit, FAISS, Groq and OCR</div>',
    unsafe_allow_html=True,
)
