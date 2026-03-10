"""
🎓 University AI Assistant - Production-Grade Portal
Official university portal with professional branding and comprehensive features
"""
import streamlit as st
import requests
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

# Import components
from components.header import render_header
from components.profile_card import render_profile_card
from components.chat_bubble import render_chat_message, render_typing_indicator
from components.quick_actions import render_quick_actions
from components.toast import show_toast
from styles.custom_css import UNIVERSITY_CSS
from suggestion_ui import display_suggestions_panel, display_dashboard

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page Configuration
st.set_page_config(
    page_title="University AI Assistant Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"  # Changed from collapsed
)

# Apply Custom CSS
st.markdown(UNIVERSITY_CSS, unsafe_allow_html=True)

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Any:
    """Call FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def create_session_id(student_id: str) -> str:
    """Create consistent session ID from student ID."""
    return hashlib.md5(student_id.lower().encode()).hexdigest()


def load_student_profile(student_id: str) -> Dict:
    """Load student profile from backend."""
    try:
        profile_data = call_api(f"/api/profile/{student_id}")
        if profile_data and profile_data.get("profile"):
            return profile_data["profile"]
        return {"student_id": student_id}
    except:
        return {"student_id": student_id}


def load_chat_history(session_id: str):
    """Load conversation history from backend."""
    try:
        history = call_api(f"/api/chat/history/{session_id}")
        if history and history.get("messages"):
            messages = []
            for msg in history["messages"]:
                messages.append({
                    "role": "user" if msg["type"] == "human" else "assistant",
                    "content": msg["content"]
                })
            st.session_state.messages = messages
            show_toast(f"Loaded {len(messages)} previous messages", "success")
    except Exception as e:
        st.session_state.messages = []


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "system_status" not in st.session_state:
    st.session_state.system_status = "online"
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False


# ==============================================================================
# PHASE 1: LOGIN / REGISTRATION
# ==============================================================================

if not st.session_state.logged_in:
    # Render header (no student name yet)
    render_header(status="online")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Check if showing registration form
        if not st.session_state.get("show_registration", False):
            # STEP 1: Login or Create Account
            st.markdown("## 🎓 Student Portal")
            
            tab1, tab2 = st.tabs(["🔐 Login", "✨ Create Account"])
            
            with tab1:
                st.markdown("### Returning Student")
                student_id_input = st.text_input("Student ID", placeholder="e.g., 10843168", key="login_id")
                
                if st.button("🚀 Login", use_container_width=True, type="primary", key="login_btn"):
                    if student_id_input:
                        # Check if profile exists
                        profile = load_student_profile(student_id_input)
                        
                        if profile.get("name") and profile.get("program"):
                            # Returning student - login directly
                            session_id = create_session_id(student_id_input)
                            st.session_state.session_id = session_id
                            st.session_state.student_id = student_id_input
                            st.session_state.student_profile = profile
                            st.session_state.logged_in = True
                            
                            # Load chat history
                            load_chat_history(session_id)
                            
                            show_toast(f"Welcome back, {profile.get('name')}!", "success")
                            st.rerun()
                        else:
                            st.error("⚠️ Student ID not found. Please create a new account.")
                    else:
                        st.error("Please enter your Student ID")
            
            with tab2:
                st.markdown("### New Student Registration")
                new_id = st.text_input("Student ID", placeholder="e.g., 10843168", key="new_id")
                
                if st.button("📝 Continue to Registration", use_container_width=True, type="primary", key="new_btn"):
                    if new_id:
                        st.session_state.show_registration = True
                        st.session_state.temp_student_id = new_id
                        st.rerun()
                    else:
                        st.error("Please enter your Student ID")
        
        else:
            # STEP 2: Registration Form (only for new students)
            st.markdown("## 📝 Complete Your Profile")
            st.caption(f"Creating account for ID: {st.session_state.temp_student_id}")
            
            with st.form("registration_form"):
                full_name = st.text_input("Full Name *", placeholder="e.g., Shubham Yadav")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    program = st.selectbox("Program *", ["BTech", "MTech", "PhD", "MBA"])
                with col_b:
                    branch = st.selectbox("Branch *", [
                        "Computer Science", "Information Technology", 
                        "Electronics", "Mechanical", "Civil", "AI & Data Science"
                    ])
                
                col_c, col_d = st.columns(2)
                with col_c:
                    year = st.number_input("Year", min_value=1, max_value=5, value=1)
                with col_d:
                    semester = st.number_input("Semester", min_value=1, max_value=10, value=1)
                
                col_submit, col_back = st.columns(2)
                with col_submit:
                    submit = st.form_submit_button("✅ Create Account", use_container_width=True)
                with col_back:
                    back = st.form_submit_button("⬅️ Back", use_container_width=True)
                
                if back:
                    st.session_state.show_registration = False
                    st.rerun()
                
                if submit:
                    if full_name:
                        # Create session
                        session_id = create_session_id(st.session_state.temp_student_id)
                        st.session_state.session_id = session_id
                        st.session_state.student_id = st.session_state.temp_student_id
                        
                        # Create profile
                        profile = {
                            "student_id": st.session_state.temp_student_id,
                            "name": full_name,
                            "program": program,
                            "department": branch,
                            "year": year,
                            "semester": semester
                        }
                        
                        st.session_state.student_profile = profile
                        st.session_state.logged_in = True
                        st.session_state.show_registration = False
                        
                        show_toast(f"Account created! Welcome, {full_name}!", "success")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")

# ==============================================================================
# PHASE 2: MAIN APPLICATION
# ==============================================================================

else:
    profile = st.session_state.student_profile
    
    # SIDEBAR FIRST - Render before anything else
    with st.sidebar:
        # Profile Card
        render_profile_card(profile)
        
        st.divider()
        
        # View Selector
        st.markdown("### 📋 Navigation")
        view = st.radio(
            "Select View",
            ["💬 Chat", "📊 Dashboard", "🎯 Suggestions"],
            label_visibility="collapsed"
        )
        
        if "💬 Chat" in view:
            st.session_state.current_view = "chat"
        elif "📊 Dashboard" in view:
           st.session_state.current_view = "dashboard"
        else:
            st.session_state.current_view = "suggestions"
        
        st.divider()
        
        # Quick Actions
        action = render_quick_actions()
        if action:
            st.rerun()
        
        st.divider()
        
        # Session Controls
        st.markdown("### ⚙️ Session")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            try:
                # Call backend to delete from Redis
                response = requests.delete(
                    f"{API_BASE_URL}/api/chat/history/{st.session_state.session_id}",
                    timeout=5
                )
                if response.status_code == 200:
                    st.session_state.messages = []
                    show_toast("Chat history cleared permanently", "success")
                else:
                    st.session_state.messages = []
                    show_toast("Chat cleared locally", "warning")
            except Exception as e:
                st.session_state.messages = []
                show_toast(f"Chat cleared (backend unavailable)", "warning")
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.student_profile = {}
            st.session_state.messages = []
            st.rerun()
    
    # NOW render header
    render_header(
        student_name=profile.get('name', 'Student'),
        status=st.session_state.system_status
    )
    
    # Main Content Area
    if st.session_state.current_view == "chat":
        # CHAT VIEW
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat messages
        for idx, message in enumerate(st.session_state.messages):
            render_chat_message(
                role=message["role"],
                content=message["content"],
                agent_type=message.get("agent_type", "general")
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat Input
        user_input = st.chat_input("Ask me anything about university...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Show typing indicator
            with st.spinner(""):
                st.session_state.system_status = "thinking"
                
                # Call API
                response = call_api(
                    "/api/chat/",
                    method="POST",
                    data={
                        "query": user_input,
                        "session_id": st.session_state.session_id
                    }
                )
                
                st.session_state.system_status = "online"
                
                if response:
                    # Add assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.get("answer", "Sorry, I couldn't process that."),
                        "agent_type": "rag"
                    })
                else:
                    st.error("Failed to get response from backend")
            
            st.rerun()
    
    elif st.session_state.current_view == "dashboard":
        # DASHBOARD VIEW
        display_dashboard(st.session_state.student_id, API_BASE_URL)
    
    else:
        # SUGGESTIONS VIEW
        display_suggestions_panel(st.session_state.student_id, API_BASE_URL)
    
    # Footer
    st.markdown("""
    <div class="university-footer">
        © 2025 University AI Assistant. All Rights Reserved. | Powered by Advanced AI
    </div>
    """, unsafe_allow_html=True)
