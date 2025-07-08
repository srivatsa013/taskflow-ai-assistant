# pages/3_🤖_Chatbot.py
import streamlit as st
import openai
from datetime import date
# Import your existing, working functions from utils.py
from utils import apply_global_styles, build_sidebar, add_task, get_tasks, delete_task

# --- Page Config & Setup ---
st.set_page_config(page_title="TaskFlow Assistant", page_icon="🤖", layout="wide")
apply_global_styles(); build_sidebar()
if not st.session_state.get("login_state"):
    st.switch_page("taskflow_app.py")

st.title("🤖 TaskFlow AI Assistant")
st.markdown("Ask me to 'add task learn python', 'delete task learn python', or ask me anything else!")

# --- SECURE API KEY SETUP ---
# This reads the key from your .streamlit/secrets.toml file and is SAFE to push to GitHub.
try:
    client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
except (KeyError, FileNotFoundError):
    st.error("OpenAI API key not found. Please create and populate your .streamlit/secrets.toml file.", icon="🚨"); st.stop()

# --- HYBRID CHATBOT LOGIC ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def handle_hybrid_command(user_input):
    """
    This function first tries to handle simple commands locally.
    If it doesn't recognize the command, it passes the request to OpenAI.
    """
    input_lower = user_input.lower()
    username = st.session_state.username

    # --- Local Commands (Fast and Cheap) ---
    if input_lower.startswith("add task"):
        # Extracts the task title from "add task [title]"
        task_title = user_input[9:].strip()
        if task_title:
            # We use your existing add_task function with default values
            add_task(username, task_title, "Medium", date.today().isoformat(), ["chatbot"])
            return f"✅ Task '{task_title}' was added successfully!"
        else:
            return "Please specify the task to add after 'add task'."

    elif input_lower.startswith("delete task"):
        task_title_to_delete = user_input[12:].strip()
        if task_title_to_delete:
            all_tasks = get_tasks(username)
            # Find the first task that matches the title (case-insensitive)
            task_found = None
            for t in all_tasks:
                if t['title'].lower() == task_title_to_delete.lower():
                    task_found = t
                    break
            
            if task_found:
                delete_task(str(task_found['_id']))
                return f"🗑️ Task '{task_found['title']}' was deleted successfully!"
            else:
                return f"❓ Task '{task_title_to_delete}' not found."
        else:
            return "Please specify the task to delete after 'delete task'."

    # --- OpenAI Fallback (For everything else) ---
    else:
        with st.spinner("Thinking..."):
            try:
                # Build the message history for context
                messages = [{"role": "system", "content": "You are a helpful assistant."}]
                for msg in st.session_state.chat_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                messages.append({"role": "user", "content": user_input})
                
                # Make the API call
                response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
                bot_reply = response.choices[0].message.content
                return bot_reply
            except openai.RateLimitError:
                return "I'm experiencing high traffic right now. Please check your OpenAI billing details or try again later."
            except Exception as e:
                return f"An error occurred: {e}"

# --- Chat Interface ---
# Display previous messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Get new user input
if prompt := st.chat_input("Ask your assistant..."):
    # Add user message to history and display it
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get and display the bot's reply
    bot_reply = handle_hybrid_command(prompt)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)
    
    # Rerun to clear the input box and show the latest messages correctly
    st.rerun()