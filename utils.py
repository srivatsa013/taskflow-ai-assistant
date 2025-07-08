# utils.py
import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
import re

# --- DB and User Functions (Unchanged) ---
@st.cache_resource
def get_mongo_client(): MONGO_URI = st.secrets["mongo"]["uri"]; client = MongoClient(MONGO_URI); return client
def get_db(): client = get_mongo_client(); return client["taskflow_db"]
def get_tasks_collection(): db = get_db(); return db["tasks"]
def get_users_collection(): db = get_db(); return db["users"]
def create_user(username, password):
    users_col = get_users_collection()
    if len(username) < 3: return "Username must be at least 3 characters long."
    if len(password) < 4: return "Password must be at least 4 characters long."
    if not re.match("^[a-zA-Z0-9_]+$", username): return "Username can only contain letters, numbers, and underscores."
    if users_col.find_one({"username": username}): return "Username already exists."
    users_col.insert_one({"username": username, "password": password}); return True
def authenticate_user(username, password):
    users_col = get_users_collection(); user_data = users_col.find_one({"username": username})
    if user_data and user_data["password"] == password: return user_data
    return None
def add_task(username: str, title: str, priority: str, due_date: str, tags: list):
    tasks_col = get_tasks_collection(); tasks_col.insert_one({"username": username, "title": title, "status": "Pending", "priority": priority, "due_date": due_date, "tags": tags, "created_at": datetime.utcnow()})
def get_tasks(username: str):
    tasks_col = get_tasks_collection(); return list(tasks_col.find({"username": username}))
def update_task_status(task_id: str, new_status: str):
    tasks_col = get_tasks_collection(); tasks_col.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": new_status}})
def delete_task(task_id: str):
    tasks_col = get_tasks_collection(); tasks_col.delete_one({"_id": ObjectId(task_id)})
def update_task_details(task_id: str, new_priority: str, new_due_date: str, new_tags: list):
    tasks_col = get_tasks_collection(); tasks_col.update_one({"_id": ObjectId(task_id)}, {"$set": {"priority": new_priority, "due_date": new_due_date, "tags": new_tags}})
def update_task_by_title(username: str, title: str, new_status: str = None, new_priority: str = None, new_tags: list = None):
    tasks_col = get_tasks_collection(); query = {"username": username, "title": {"$regex": title, "$options": "i"}}; matching_tasks = list(tasks_col.find(query))
    if len(matching_tasks) == 0: return f"Error: I couldn't find any task containing the title '{title}'."
    if len(matching_tasks) > 1: found_titles = [f"'{t['title']}'" for t in matching_tasks]; return f"Error: I found multiple tasks that match: {', '.join(found_titles)}. Please be more specific."
    task_to_update = matching_tasks[0]; task_id = task_to_update["_id"]; update_data = {};
    if new_status: update_data["status"] = new_status
    if new_priority: update_data["priority"] = new_priority
    if new_tags is not None: update_data["tags"] = new_tags
    if not update_data: return "No new information was provided to update the task."
    result = tasks_col.update_one({"_id": task_id}, {"$set": update_data})
    if result.modified_count > 0: return f"Successfully updated the task: '{task_to_update['title']}'."
    else: return f"The task '{task_to_update['title']}' already had these properties. No update was necessary."

# --- THEME & CSS ---
def get_era_theme_config(era):
    themes = {
        "1989": {"bg": "#e0f7fa", "text": "#0d47a1", "btn_bg": "#1976d2", "btn_text": "#ffffff", "cal_bg": "#b3e5fc", "cal_text": "#01579b", "btn_hover": "#1565c0"},
        "Red": {"bg": "#fff0f0", "text": "#c1121f", "btn_bg": "#d32f2f", "btn_text": "#ffffff", "cal_bg": "#ffcdd2", "cal_text": "#b71c1c", "btn_hover": "#c62828"},
        "Lover": {"bg": "#ffe6f0", "text": "#c2185b", "btn_bg": "#ec407a", "btn_text": "#ffffff", "cal_bg": "#f8bbd0", "cal_text": "#880e4f", "btn_hover": "#d81b60"},
        "Folklore": {"bg": "#f0f0f0", "text": "#4a4a4a", "btn_bg": "#757575", "btn_text": "#ffffff", "cal_bg": "#e0e0e0", "cal_text": "#333333", "btn_hover": "#616161"}
    }
    return themes.get(era, themes["Folklore"])

def apply_global_styles():
    if "era_mode" not in st.session_state: st.session_state.era_mode = "Folklore"
    current_theme = get_era_theme_config(st.session_state.era_mode)
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        .stApp {{ background-color: {current_theme['bg']}; }}
        body {{ font-family: 'Poppins', sans-serif; }}
        
        /* --- THIS IS THE FIX --- */
        /* Targets st.title, h1 from markdown */
        .themed-title {{ color: {current_theme['text']} !important; font-weight: 700; font-size: 2.25rem; }}
        /* Targets st.subheader, h2 from markdown */
        .themed-subheader {{ color: {current_theme['text']} !important; font-weight: 600; font-size: 1.5rem; }}
        
        .stButton > button {{ background-color: {current_theme['btn_bg']}; color: {current_theme['btn_text']}; border-radius: 8px; border: none; }}
        .logout-button-container .stButton > button {{ background-color: #d32f2f !important; }}
        .logout-button-container .stButton > button p {{ color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR LOGIC ---
def build_sidebar():
    if not st.session_state.get("login_state"): return
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.get('user', '')}")
        st.markdown(f'<div class="logout-button-container">', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True); st.markdown("---")
        
        # --- THIS IS THE FIX ---
        # Use st.subheader to apply the themed style automatically
        st.subheader("🎨 Choose Your Era")
        
        era_options = ["Folklore", "Lover", "Red", "1989"]
        selected_era = st.selectbox("Era Select", era_options, label_visibility="collapsed", index=era_options.index(st.session_state.get("era_mode", "Folklore")))
        if selected_era != st.session_state.get("era_mode"):
            st.session_state.era_mode = selected_era; st.rerun()
        st.markdown("---")
        
        st.subheader("Stats at a Glance")
        all_tasks = get_tasks(st.session_state.user); total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t['status'] == 'Completed'])
        st.metric("Pending Tasks", total_tasks - completed_tasks); st.metric("Completed Tasks", completed_tasks)