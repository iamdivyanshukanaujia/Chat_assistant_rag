"""
Student Profile Card Component
"""
import streamlit as st
from typing import Dict, Any


def render_profile_card(profile: Dict[str, Any]):
    """
    Render student profile card with avatar and stats.
    
    Args:
        profile: Student profile dictionary with name, id, program, etc.
    """
    name = profile.get('name', 'Student')
    student_id = profile.get('student_id', 'N/A')
    program = profile.get('program', 'N/A')
    department = profile.get('department', 'N/A')
    year = profile.get('year', 'N/A')
    cgpa = profile.get('cgpa', 0.0)
    attendance = profile.get('attendance_percentage', 0)
    
    # Get initials for avatar
    initials = ''.join([word[0].upper() for word in name.split()[:2]]) if name != 'Student' else 'ST'
    
    profile_html = f"""
    <div class="profile-card">
        <div class="profile-header">
            <div class="profile-avatar">{initials}</div>
            <div class="profile-info">
                <h3>{name}</h3>
                <p>ID: {student_id}</p>
                <p>{program} • {department}</p>
                <p>Year {year}</p>
            </div>
        </div>
        <div class="profile-stats">
            <div class="stat-item">
                <div class="stat-value">{cgpa:.1f}</div>
                <div class="stat-label">CGPA</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{attendance}%</div>
                <div class="stat-label">Attendance</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(profile_html, unsafe_allow_html=True)
