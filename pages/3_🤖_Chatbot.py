# pages/3_🤖_Chatbot.py
import streamlit as st
import openai
import json
from datetime import date
from utils import (
    apply_global_styles, build_sidebar, add_task, get_tasks, 
    update_task_by_title, delete_task_by_title
)

st.set_page_config(page_title="TaskFlow Assistant", page_icon="🤖", layout="wide")
apply_global_styles(); build_sidebar()
if not st.session_state.get("login_state"):
    st.switch_page("taskflow_app.py")

st.markdown("<h1 class='themed-title'>🤖 TaskFlow AI Assistant</h1>", unsafe_allow_html=True)
st.markdown("Try 'add task call mom tomorrow high priority', 'show my pending tasks', or 'delete task call mom'.")

if "confirmation_message" in st.session_state:
    st.toast(st.session_state.confirmation_message, icon="✅")
    del st.session_state.confirmation_message

try:
    client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
except (KeyError, FileNotFoundError):
    st.error("OpenAI API key not found.", icon="🚨"); st.stop()

tools = [
    {"type": "function", "function": {"name": "get_tasks", "description": "Get a list of all of the user's tasks.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "add_task", "description": "Add a new task. Today's date is " + str(date.today()), "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "priority": {"type": "string", "enum": ["High", "Medium", "Low"]}, "due_date": {"type": "string", "description": "YYYY-MM-DD format."}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["title", "due_date"]}}},
    {"type": "function", "function": {"name": "update_task_by_title", "description": "Update a task's status, priority, due date, or tags.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "new_status": {"type": "string", "enum": ["Pending", "Completed"]}, "new_priority": {"type": "string", "enum": ["High", "Medium", "Low"]}, "new_due_date": {"type": "string"}, "new_tags": {"type": "array", "items": {"type": "string"}}}, "required": ["title"]}}},
    {"type": "function", "function": {"name": "delete_task_by_title", "description": "Delete a task by its title, with optional filters.", "parameters": {"type": "object", "properties": {"title": {"type": "string"},"priority": {"type": "string", "enum": ["High", "Medium", "Low"]}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["title"]}}},
]
available_functions = {"get_tasks": get_tasks, "add_task": add_task, "update_task_by_title": update_task_by_title, "delete_task_by_title": delete_task_by_title}

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you manage your tasks today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"];
        if isinstance(content, list):
            if len(content) > 0:
                formatted_list = [f"- **{item['title']}** (Priority: {item.get('priority', 'N/A')}, Due: {item.get('due_date', 'N/A')})" for item in content]
                st.markdown("\n".join(formatted_list))
            else:
                st.markdown("I couldn't find any tasks that match.")
        else:
            st.markdown(str(content))

if prompt := st.chat_input("Ask your assistant..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                base_messages = [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages]
                response = client.chat.completions.create(model="gpt-3.5-turbo", messages=base_messages, tools=tools, tool_choice="auto")
                response_message = response.choices[0].message; tool_calls = response_message.tool_calls
                if tool_calls:
                    base_messages.append(response_message)
                    needs_data_refresh = False
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_to_call = available_functions[function_name]
                        function_args = json.loads(tool_call.function.arguments)
                        function_args["username"] = st.session_state.user
                        if function_name in ["add_task", "update_task_by_title", "delete_task_by_title"]:
                            needs_data_refresh = True
                        if function_name == "add_task": function_args.setdefault("priority", "Medium"); function_args.setdefault("tags", [])
                        function_response = function_to_call(**function_args)
                        base_messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": str(function_response)})
                    
                    second_response = client.chat.completions.create(model="gpt-3.5-turbo", messages=base_messages)
                    full_response = second_response.choices[0].message.content
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    if needs_data_refresh:
                        st.session_state.confirmation_message = full_response
                        st.rerun() # Rerun the current page to refresh sidebar and show toast
                else:
                    full_response = response.choices[0].message.content
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
            except openai.RateLimitError:
                st.error("API quota exceeded."); st.stop()
            except Exception as e:
                st.error(f"An error occurred: {e}"); st.stop()