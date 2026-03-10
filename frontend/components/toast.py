"""
Toast Notification Component
"""
import streamlit as st
import time


def show_toast(message: str, toast_type: str = "info", duration: int = 3):
    """
    Show a toast notification.
    
    Args:
        message: Toast message
        toast_type: 'success', 'error', or 'info'
        duration: Display duration in seconds
    """
    toast_html = f"""
    <div class="toast {toast_type}" style="display: block;" id="toast-notification">
        {message}
    </div>
    <script>
        setTimeout(function() {{
            document.getElementById('toast-notification').style.display = 'none';
        }}, {duration * 1000});
    </script>
    """
    
    st.markdown(toast_html, unsafe_allow_html=True)
    
    # Also use Streamlit's native toast
    if toast_type == "success":
        st.toast(message, icon="✅")
    elif toast_type == "error":
        st.toast(message, icon="❌")
    else:
        st.toast(message, icon="ℹ️")
