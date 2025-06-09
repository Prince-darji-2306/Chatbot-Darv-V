import os
import streamlit as st
from groq import Groq


client = Groq(api_key=st.secrets["GROQ_API_KEY"])
config = st.secrets['CONFIG']
tone = st.secrets['THINK']
st.set_page_config(page_title="Darv-V GPT", layout="wide")

st.markdown("""
    <style>
        /* Decrease sidebar width */
        [data-testid="stSidebar"] {
            width: 260px !important;
        }
        /* Adjust the space between sidebar and main */
        section[data-testid="stSidebar"] > div {
            padding-right: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1px;
            padding-bottom: -10px;
        }
    </style>
""", unsafe_allow_html=True)

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
    # Title: use first user prompt or fallback
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

# Ensure valid chat state after deletion or initialization
if not st.session_state.chat_history:
    # No chats left → create a new one
    st.session_state.chat_history.append([])
    st.session_state.selected_chat = 0
    rerun_needed = True
else:
    # Ensure selected_chat index is within valid bounds
    max_index = len(st.session_state.chat_history) - 1
    if st.session_state.selected_chat is None or st.session_state.selected_chat > max_index:
        st.session_state.selected_chat = max_index
        rerun_needed = True


if rerun_needed:
    st.rerun()

# Current chat
current_chat = st.session_state.chat_history[st.session_state.selected_chat]



# --- Main Chat Interface ---
st.title("🧠 Ask Darv-V")
st.caption("Chatbot app with Live Response and Thinking")

for role, msg in current_chat:
    with st.chat_message(role):
        st.markdown(msg)

prompt = st.chat_input("Type your message...")
    
def is_markdown_sensitive(text):
        return any(sym in text for sym in ['#', '*', '-', '>'])

if prompt:
    current_chat.append(("user", prompt))

    # Show user input
    with st.chat_message("user"):
        if is_markdown_sensitive(prompt):
            st.code(prompt,language='text')
        else:
            st.markdown(prompt)

    # Placeholders for thinking and assistant response
    thinking_box = st.empty()
    ai_box = st.empty()

    collected_resp = ""
    thinking_resp = ""
    inside_think = False

    # Stream response from API
    response = client.chat.completions.create(
    model="deepseek-r1-distill-llama-70b",
    temperature = 0.4,
    max_tokens= 3048,
    messages=([{'role': 'system', 'content': config}] +
             [{'role': 'system', 'content': tone}]  + 
             [{"role": role, "content": msg} for role, msg in current_chat]),
    stream=True,
    )

    for chunk in response:
        content = chunk.choices[0].delta.content or ""

        # Handle <think> tags
        if "<think>" in content:
            inside_think = True
            content = content.replace("<think>", "")
        if "</think>" in content:
            inside_think = False
            content = content.replace("</think>", "")

        if inside_think:
            thinking_resp += content
            # Render with scrollable div
            thinking_box.markdown(
                f"""
                <div style="max-height: 100px; overflow-y: auto; background-color: #f1f1f1; padding: 6px 10px; font-size: 0.85em; border-radius: 6px; border: 1px solid #ddd;">
                    🧠 <i>{thinking_resp}</i>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            collected_resp += content
            ai_box.markdown(collected_resp)

    thinking_box.empty()  # Hide once done
    current_chat.append(("assistant", collected_resp))