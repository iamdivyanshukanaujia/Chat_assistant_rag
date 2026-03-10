"""
Sticky Header Component for University Portal
"""
import streamlit as st


def render_header(student_name: str = None, status: str = "online"):
    """
    Render sticky university header with branding and status indicator.
    
    Args:
        student_name: Current logged in student name
        status: System status - 'online', 'thinking', or 'offline'
    """
    status_icons = {
        "online": "🟢",
        "thinking": "🟡",
        "offline": "🔴"
    }
    
    status_text = {
        "online": "Online",
        "thinking": "Thinking...",
        "offline": "Offline"
    }
    
    # Add sidebar toggle button
    col1, col2 = st.columns([1, 20])
    with col1:
        if st.button("☰", key="sidebar_toggle", help="Toggle Sidebar"):
            pass  # Streamlit handles sidebar toggle automatically
    
    header_html = f"""
    <div class="university-header">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div class="logo">🎓</div>
            <h1>University AI Assistant</h1>
        </div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <div class="status-indicator">
                <span class="dot status-{status}"></span>
                <span>{status_icons.get(status, '🔵')} {status_text.get(status, 'Unknown')}</span>
            </div>
            {f'<div style="color: white; font-size: 14px;">👤 {student_name}</div>' if student_name else ''}
        </div>
    </div>
    """
    
    with col2:
        st.markdown(header_html, unsafe_allow_html=True)
