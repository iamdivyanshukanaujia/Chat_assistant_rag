"""
Custom CSS Styles for University AI Assistant Portal
Official university branding with deep blue and gold colors
"""

UNIVERSITY_CSS = """
<style>
/* ===============================================
   UNIVERSITY BRANDING - COLOR PALETTE
   =============================================== */
:root {
    --university-blue: #003366;
    --university-gold: #FFB81C;
    --university-light-blue: #0056b3;
    --university-dark-blue: #001f3f;
    
    --primary-bg: #ffffff;
    --secondary-bg: #f8f9fa;
    --tertiary-bg: #e9ecef;
    
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --text-light: #adb5bd;
    
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    --info: #17a2b8;
    
    --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.2);
    
    --border-radius: 8px;
    --transition: all 0.3s ease;
}

/* ===============================================
   GLOBAL STYLES & TYPOGRAPHY
   =============================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.main {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 0;
}

/* Keep sidebar toggle visible - don't hide MainMenu completely */
footer {visibility: hidden;}
header {visibility: hidden;}

/* ===============================================
   STICKY HEADER
   =============================================== */
.university-header {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: linear-gradient(135deg, var(--university-blue) 0%, var(--university-dark-blue) 100%);
    padding: 20px 40px;
    box-shadow: var(--shadow-lg);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.university-header h1 {
    color: white;
    font-size: 24px;
    font-weight: 600;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 15px;
}

.university-header .logo {
    width: 50px;
    height: 50px;
    background: var(--university-gold);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    color: white;
    font-size: 14px;
}

.status-indicator .dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

.status-online { background: var(--success); }
.status-thinking { background: var(--warning); }
.status-offline { background: var(--danger); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ===============================================
   CHAT BUBBLES
   =============================================== */
.chat-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

.chat-message {
    display: flex;
    margin-bottom: 20px;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.chat-message.user {
    justify-content: flex-end;
}

.chat-message.assistant {
    justify-content: flex-start;
}

.chat-bubble {
    max-width: 70%;
    padding: 15px 20px;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-sm);
    position: relative;
}

.chat-message.user .chat-bubble {
    background: linear-gradient(135deg, var(--university-blue) 0%, var(--university-light-blue) 100%);
    color: white;
    border-bottom-right-radius: 4px;
}

.chat-message.assistant .chat-bubble {
    background: white;
    color: var(--text-primary);
    border-bottom-left-radius: 4px;
    border: 1px solid #e0e0e0;
}

.chat-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin: 0 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: var(--shadow-sm);
}

.chat-message.user .chat-avatar {
    background: var(--university-gold);
    order: 2;
}

.chat-message.assistant .chat-avatar {
    background: var(--university-blue);
    color: white;
}

.message-time {
    font-size: 11px;
    color: var(--text-light);
    margin-top: 5px;
}

/* ===============================================
   AGENT INDICATORS
   =============================================== */
.agent-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 8px;
    background: var(--tertiary-bg);
    color: var(--text-secondary);
}

.agent-badge.rag { background: #e3f2fd; color: #1976d2; }
.agent-badge.syllabus { background: #f3e5f5; color: #7b1fa2; }
.agent-badge.attendance { background: #fff3e0; color: #ef6c00; }
.agent-badge.placement { background: #e8f5e9; color: #388e3c; }

/* ===============================================
   PROFILE CARD
   =============================================== */
.profile-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 20px;
    box-shadow: var(--shadow-md);
    margin-bottom: 20px;
}

.profile-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
}

.profile-avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--university-blue), var(--university-light-blue));
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 600;
}

.profile-info h3 {
    margin: 0;
    font-size: 18px;
    color: var(--text-primary);
}

.profile-info p {
    margin: 2px 0;
    font-size: 13px;
    color: var(--text-secondary);
}

.profile-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.stat-item {
    background: var(--secondary-bg);
    padding: 10px;
    border-radius: 6px;
    text-align: center;
}

.stat-value {
    font-size: 20px;
    font-weight: 700;
    color: var(--university-blue);
}

.stat-label {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
}

/* ===============================================
   QUICK ACTIONS
   =============================================== */
.quick-actions {
    margin-top: 20px;
}

.action-btn {
    width: 100%;
    padding: 12px;
    margin-bottom: 8px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    text-align: left;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-primary);
}

.action-btn:hover {
    background: var(--secondary-bg);
    border-color: var(--university-blue);
    transform: translateX(4px);
}

.action-btn .icon {
    font-size: 18px;
}

/* ===============================================
   TYPING ANIMATION
   =============================================== */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 10px;
}

.typing-indicator .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-light);
    animation: typing 1.4s infinite;
}

.typing-indicator .dot:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator .dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.7;
    }
    30% {
        transform: translateY(-10px);
        opacity: 1;
    }
}

/* ===============================================
   BUTTONS & INPUTS
   =============================================== */
.stButton button {
    background: linear-gradient(135deg, var(--university-blue), var(--university-light-blue)) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

.stTextInput input, .stSelectbox select {
    border-radius: 6px !important;
    border: 1px solid #e0e0e0 !important;
    padding: 10px !important;
}

.stTextInput input:focus, .stSelectbox select:focus {
    border-color: var(--university-blue) !important;
    box-shadow: 0 0 0 2px rgba(0, 51, 102, 0.1) !important;
}

/* ===============================================
   TOAST NOTIFICATIONS
   =============================================== */
.toast {
    position: fixed;
    top: 80px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 6px;
    box-shadow: var(--shadow-lg);
    animation: slideInRight 0.3s ease;
    z-index: 9999;
}

@keyframes slideInRight {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.toast.success { background: var(--success); color: white; }
.toast.error { background: var(--danger); color: white; }
.toast.info { background: var(--info); color: white; }

/* ===============================================
   FOOTER
   =============================================== */
.university-footer {
    background: var(--university-dark-blue);
    color: white;
    text-align: center;
    padding: 15px;
    font-size: 13px;
    margin-top: 40px;
}

/* ===============================================
   DARK MODE
   =============================================== */
.dark-mode {
    --primary-bg: #1a1a1a;
    --secondary-bg: #2d2d2d;
    --tertiary-bg: #3d3d3d;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --text-light: #808080;
}

.dark-mode .chat-message.assistant .chat-bubble {
    background: #2d2d2d;
    border-color: #404040;
    color: white;
}

.dark-mode .profile-card {
    background: #2d2d2d;
}

.dark-mode .action-btn {
    background: #2d2d2d;
    border-color: #404040;
    color: white;
}

/* ===============================================
   RESPONSIVE DESIGN
   =============================================== */
@media (max-width: 768px) {
    .university-header {
        padding: 15px 20px;
    }
    
    .university-header h1 {
        font-size: 18px;
    }
    
    .chat-bubble {
        max-width: 85%;
    }
    
    .profile-stats {
        grid-template-columns: 1fr;
    }
}

/* ===============================================
   CUSTOM SCROLLBAR
   =============================================== */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--secondary-bg);
}

::-webkit-scrollbar-thumb {
    background: var(--university-blue);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--university-light-blue);
}
</style>
"""
