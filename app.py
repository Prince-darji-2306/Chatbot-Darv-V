import os
import streamlit as st
from groq import Groq

# Set page config
st.set_page_config(page_title="Darv-V | AI That Thinks Before It Speaks", layout="wide", page_icon='static/img/Icon.png')

# Inject CSS from external file
def load_local_css(file_name):
    with open(file_name) as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

load_local_css("static/css/cstyle.css")

# Apply body wrapper classes
st.markdown('<div class="custom-sidebar custom-container">', unsafe_allow_html=True)

# --- API and session setup ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
config = st.secrets['CONFIG']
tone = st.secrets['THINK']

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None

st.sidebar.title("💬 Your Chats")
rerun_needed = False

# Add new chat
if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_history.append([])
    st.session_state.selected_chat = len(st.session_state.chat_history) - 1
    rerun_needed = True

chats_to_delete = []
for idx, chat in enumerate(st.session_state.chat_history):
    title = next((msg for role, msg in chat if role == "user"), f"Chat {idx + 1}")
    col1, col2 = st.sidebar.columns([0.8, 0.2])
    if col1.button(title[:30] + ("..." if len(title) > 30 else ""), key=f"title_{idx}"):
        st.session_state.selected_chat = idx
        rerun_needed = True
    if col2.button("🗑", key=f"delete_{idx}"):
        chats_to_delete.append(idx)

for idx in sorted(chats_to_delete, reverse=True):
    del st.session_state.chat_history[idx]
    if st.session_state.selected_chat == idx:
        st.session_state.selected_chat = None
    rerun_needed = True

if not st.session_state.chat_history:
    st.session_state.chat_history.append([])
    st.session_state.selected_chat = 0
    rerun_needed = True
else:
    max_index = len(st.session_state.chat_history) - 1
    if st.session_state.selected_chat is None or st.session_state.selected_chat > max_index:
        st.session_state.selected_chat = max_index
        rerun_needed = True

if rerun_needed:
    st.rerun()

# Current chat
current_chat = st.session_state.chat_history[st.session_state.selected_chat]

# --- Main Chat Interface ---
st.title("🧠Ask Darv-V")
st.caption("Chatbot app with Live Response and Thinking")

for role, msg in current_chat:
    with st.chat_message(role):
        st.markdown(msg)

prompt = st.chat_input("Type your message...")

def is_markdown_sensitive(text):
    return any(sym in text for sym in ['#', '*', '-', '>'])

if prompt:
    current_chat.append(("user", prompt))

    # Display user prompt
    with st.chat_message("user"):
        if is_markdown_sensitive(prompt):
            st.code(prompt, language='text')
        else:
            st.markdown(prompt)

    thinking_box = st.empty()
    ai_box = st.empty()

    collected_resp = ""
    thinking_resp = ""
    inside_think = False

    response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        temperature=0.4,
        max_tokens=2048,
        messages=(
            [{'role': 'system', 'content': config}] +
            [{'role': 'system', 'content': tone}] +
            [{"role": role, "content": msg} for role, msg in current_chat]
        ),
        stream=True,
    )

    for chunk in response:
        content = chunk.choices[0].delta.content or ""

        if "<think>" in content:
            inside_think = True
            content = content.replace("<think>", "")
        if "</think>" in content:
            inside_think = False
            content = content.replace("</think>", "")

        if inside_think:
            thinking_resp += content
            thinking_box.markdown(
                f'<div class="thinking-box">🧠 <i>{thinking_resp}</i></div>',
                unsafe_allow_html=True
            )
        else:
            collected_resp += content
            ai_box.markdown(collected_resp)

    thinking_box.empty()
    current_chat.append(("assistant", collected_resp))

# Close custom wrapper div
st.markdown('</div>', unsafe_allow_html=True)
