"""Run with: python -m streamlit run app.py"""
import os
import streamlit as st
from portable_index import load_collection
from retrieval import answer_question
from settings import AssistantError, DEFAULT_RESPONSE_MODEL, INDEX_PATH, make_client

st.set_page_config(page_title='Arcwell HR Assistant', page_icon='💬', layout='centered')
st.markdown('''<style>
.stApp {background: #f7f9fc;}
[data-testid="stSidebar"] {background: #edf2f7;}
.block-container {max-width: 900px; padding-top: 2.5rem;}
h1, h2, h3 {color: #142d4e;}
[data-testid="stChatMessage"] {background: white; border: 1px solid #e2e8f0;
 border-radius: 14px; padding: 1.2rem;}
.eyebrow {color: #397b83; letter-spacing: .15em; font-size: .8rem; font-weight: 700;}
</style>''', unsafe_allow_html=True)


def setting(name, default=''):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


@st.cache_resource(show_spinner=False)
def handbook_collection(index_version):
    return load_collection()


def clear_chat():
    st.session_state.messages = []


def render_sources(sources):
    if not sources:
        return
    st.caption('Retrieved handbook sources • source numbers refer to this answer')
    for source in sources:
        label = f"[Source {source['source_id']}] {source['document']}"
        if source.get('page') is not None:
            label += f" · Page {source['page']}"
        if source.get('section'):
            label += f" · {source['section']}"
        st.caption(label)
    with st.expander(f"View retrieved excerpts ({len(sources)})"):
        for source in sources:
            st.markdown(f"**Source {source['source_id']}**")
            st.text(source['text'])
            st.divider()


st.session_state.setdefault('messages', [])
with st.sidebar:
    st.markdown('### ARCWELL')
    st.caption('PEOPLE OPERATIONS')
    st.divider()
    st.button('＋ New Chat', on_click=clear_chat, use_container_width=True, type='primary')
    st.button('Clear Chat', on_click=clear_chat, use_container_width=True)
    st.divider()
    st.markdown('**Your handbook, made helpful.**')
    st.caption('Explore leave, working arrangements, benefits and everyday people policies.')
    st.info('This handbook and company are fictional. For training purposes only; not legal or employment advice.')
    st.caption('Please do not enter personal or confidential employee information.')

st.markdown('<div class="eyebrow">ARCWELL / PEOPLE OPERATIONS</div>', unsafe_allow_html=True)
st.title('HR answers. A little simpler.')
st.markdown('**Arcwell HR Assistant** · Answers grounded in the employee handbook.')
collection = None
try:
    with st.spinner('Opening the handbook…'):
        collection = handbook_collection(INDEX_PATH.stat().st_mtime_ns)
except Exception:
    st.warning('The handbook is not available yet. The app owner needs to add a valid exported HR index.')
api_key = setting('OPENAI_API_KEY')
ready = collection is not None and collection.count() > 0 and bool(api_key.strip())
if collection is not None and collection.count() == 0:
    st.warning('The handbook index is empty. Please ask the app owner to update it.')
if not api_key.strip():
    st.info('The assistant is awaiting setup. The app owner needs to configure an OpenAI API key.')

suggestion = None
if not st.session_state.messages:
    st.subheader('How can I help you today?')
    st.caption('Choose a starting point, or ask your own question below.')
    questions = ['What is the annual leave policy?', 'How does parental leave work?',
                 'What are the work-from-home rules?', 'How do I claim expenses?']
    columns = st.columns(2)
    for i, question in enumerate(questions):
        if columns[i % 2].button(question, use_container_width=True, disabled=not ready):
            suggestion = question

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        if message.get('error'):
            st.error(message['content'])
        else:
            st.markdown(message['content'])
        render_sources(message.get('sources', []))

prompt = st.chat_input('Ask about the Arcwell handbook…', disabled=not ready, max_chars=2000)
if prompt or suggestion:
    question = prompt or suggestion
    history = list(st.session_state.messages)
    st.session_state.messages.append({'role': 'user', 'content': question})
    with st.chat_message('user'):
        st.markdown(question)
    with st.chat_message('assistant'):
        try:
            with st.spinner('Finding the relevant policy…'):
                with make_client(api_key) as client:
                    answer, sources = answer_question(question, collection, client,
                        setting('OPENAI_RESPONSE_MODEL', DEFAULT_RESPONSE_MODEL), history)
            st.markdown(answer)
            render_sources(sources)
            message = dict(role='assistant', content=answer, sources=sources)
        except Exception as exc:
            safe_message = str(exc) if isinstance(exc, AssistantError) else 'Something went wrong. Please try again shortly.'
            st.error(safe_message)
            message = dict(role='assistant', content=safe_message, error=True)
        st.session_state.messages.append(message)
