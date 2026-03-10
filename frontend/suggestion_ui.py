"""
Beautiful UI components for proactive suggestions in Streamlit.
"""
import streamlit as st
import requests
from typing import List, Dict


def display_suggestion_card(suggestion: Dict):
    """
    Display a single suggestion as a beautiful card.
    
    Args:
        suggestion: Suggestion dictionary with icon, title, message, priority
    """
    priority = suggestion.get("priority", "medium")
    icon = suggestion.get("icon", "💡")
    title = suggestion.get("title", "Suggestion")
    message = suggestion.get("message", "")
    action_text = suggestion.get("action_text")
    
    # Color scheme based on priority
    if priority == "critical":
        bg_color = "#FEE2E2"  # Light red
        border_color = "#DC2626"  # Red
        text_color = "#7F1D1D"  # Dark red
    elif priority == "high":
        bg_color = "#FEF3C7"  # Light yellow
        border_color = "#F59E0B"  # Amber
        text_color = "#78350F"  # Dark amber
    elif priority == "medium":
        bg_color = "#DBEAFE"  # Light blue
        border_color = "#3B82F6"  # Blue
        text_color = "#1E3A8A"  # Dark blue
    else:  # low
        bg_color = "#F3F4F6"  # Light gray
        border_color = "#9CA3AF"  # Gray
        text_color = "#374151"  # Dark gray
    
    # Create card with custom styling
    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border-left: 4px solid {border_color};
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 24px; margin-right: 10px;">{icon}</span>
            <strong style="color: {text_color}; font-size: 16px;">{title}</strong>
        </div>
        <p style="color: {text_color}; margin: 0 0 8px 34px; font-size: 14px;">{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action button if present
    if action_text:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(action_text, key=f"action_{suggestion['id']}", use_container_width=True):
                    st.info(f"Action: {action_text}")


def display_suggestions_panel(student_id: str, api_url: str, max_suggestions: int = 5):
    """
    Display proactive suggestions panel in sidebar.
    
    Args:
        student_id: Student ID
        api_url: Base API URL
        max_suggestions: Maximum suggestions to show
    """
    try:
        response = requests.get(
            f"{api_url}/api/suggestions/{student_id}",
            params={"max_results": max_suggestions},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            if suggestions:
                st.sidebar.markdown("### 💡 Important Updates")
                st.sidebar.caption(f"{len(suggestions)} notification{'s' if len(suggestions) != 1 else ''}")
                
                for suggestion in suggestions:
                    priority = suggestion.get("priority", "medium")
                    icon = suggestion.get("icon", "")
                    title = suggestion.get("title", "")
                    message = suggestion.get("message", "")
                    
                    # Display based on priority
                    if priority == "critical":
                        st.sidebar.error(f"{icon} **{title}**\n\n{message}")
                    elif priority == "high":
                        st.sidebar.warning(f"{icon} **{title}**\n\n{message}")
                    elif priority == "medium":
                        st.sidebar.info(f"{icon} **{title}**\n\n{message}")
                    else:
                        st.sidebar.write(f"{icon} **{title}**\n\n{message}")
                    
                    st.sidebar.divider()
            else:
                st.sidebar.success("✅ All caught up! No urgent items.")
        
    except Exception as e:
        st.sidebar.error(f"Unable to load suggestions: {str(e)[:50]}")


def display_dashboard(student_id: str, api_url: str):
    """
    Display a beautiful dashboard with suggestions and stats.
    
    Args:
        student_id: Student ID
        api_url: Base API URL
    """
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        text-align: center;
    ">
        <h1 style="margin: 0; font-size: 32px;">📊 Your Dashboard</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">Personalized insights and recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Fetch suggestions
        response = requests.get(
            f"{api_url}/api/suggestions/{student_id}",
            params={"max_results": 10},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            # Count by priority
            critical = sum(1 for s in suggestions if s.get("priority") == "critical")
            high = sum(1 for s in suggestions if s.get("priority") == "high")
            medium = sum(1 for s in suggestions if s.get("priority") == "medium")
            
            # Stats cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🚨 Critical", critical)
            
            with col2:
                st.metric("⚠️ High Priority", high)
            
            with col3:
                st.metric("💡 Medium", medium)
            
            with col4:
                st.metric("📊 Total", len(suggestions))
            
            st.markdown("---")
            
            # Display suggestions
            if suggestions:
                st.markdown("### 🎯 Your Personalized Updates")
                
                for suggestion in suggestions:
                    display_suggestion_card(suggestion)
            else:
                st.success("🎉 Great job! You're all caught up with no pending items.")
        
        else:
            st.error("Unable to load dashboard. Please try again.")
    
    except Exception as e:
        st.error(f"Dashboard unavailable: {str(e)}")
