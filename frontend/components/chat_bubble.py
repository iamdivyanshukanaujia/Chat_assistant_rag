"""
Chat Bubble Component
"""
import streamlit as st
from datetime import datetime


def render_chat_message(role: str, content: str, agent_type: str = None, timestamp: datetime = None):
    """
    Render a chat message bubble.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
        agent_type: Type of agent that generated response (for assistant messages)
        timestamp: Message timestamp
    """
    avatar_icons = {
        "user": "👤",
        "assistant": "🎓"
    }
    
    agent_badges = {
        "rag": ("🔍 RAG Agent", "rag"),
        "syllabus": ("📚 Syllabus Agent", "syllabus"),
        "attendance": ("🧮 Attendance Agent", "attendance"),
        "placement": ("🎯 Placement Agent", "placement"),
        "general": ("💬 General Assistant", "")
    }
    
    time_str = timestamp.strftime("%I:%M %p") if timestamp else datetime.now().strftime("%I:%M %p")
    
    message_html = f"""
    <div class="chat-message {role}">
        <div class="chat-avatar">{avatar_icons.get(role, '💬')}</div>
        <div>
            <div class="chat-bubble">
                {content}
            </div>
            <div class="message-time">{time_str}</div>
            """
    
    if role == "assistant" and agent_type:
        badge_text, badge_class = agent_badges.get(agent_type, ("", ""))
        if badge_text:
            message_html += f'<span class="agent-badge {badge_class}">{badge_text}</span>'
    
    message_html += """
        </div>
    </div>
    """
    
    st.markdown(message_html, unsafe_allow_html=True)


def render_typing_indicator():
    """Render animated typing indicator for bot thinking."""
    typing_html = """
    <div class="chat-message assistant">
        <div class="chat-avatar">🎓</div>
        <div class="chat-bubble">
            <div class="typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    </div>
    """
    st.markdown(typing_html, unsafe_allow_html=True)
