"""
Reusable UI Components for AI Career Intelligence Platform.
Provides modular visual elements matching the executive SaaS design system.
"""

import streamlit as st
from typing import List, Optional, Dict, Any


def render_header(
    title: str,
    subtitle: Optional[str] = None,
    badge_text: str = "AI Active",
    badge_color: str = "#10b981"
):
    """Render consistent page header with title, subtitle, and status badge."""
    sub_html = f'<p style="color: #64748b; font-size: 14.5px; margin: 4px 0 0 0;">{subtitle}</p>' if subtitle else ''
    html = f"""
    <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 22px; border-bottom: 1px solid #e2e8f0; padding-bottom: 14px;">
        <div>
            <h2 style="margin: 0; font-size: 24px; font-weight: 800; color: #0f172a; line-height: 1.2;">{title}</h2>
            {sub_html}
        </div>
        <div style="display: flex; align-items: center; gap: 6px; background: #ffffff; border: 1px solid #e2e8f0; padding: 4px 12px; border-radius: 9999px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
            <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {badge_color}; display: inline-block;"></span>
            <span style="font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">{badge_text}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar_brand():
    """Render modern brand identity in the sidebar."""
    html = """
    <div class="sidebar-brand-box">
        <div class="brand-icon-circle">🎙️</div>
        <div>
            <div class="brand-text-title">AI Career</div>
            <div class="brand-text-sub">Intelligence Platform</div>
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_system_status(ai_ready: bool, whisper_ready: bool, db_ready: bool):
    """Render live system status pills in the sidebar."""
    def get_dot(status: bool):
        color = "#10b981" if status else "#ef4444"
        text = "Ready" if status else "Offline"
        return f'<span style="display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:600; color:#475569;"><span style="width:7px; height:7px; border-radius:50%; background:{color};"></span>{text}</span>'

    html = f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-top: 24px;">
        <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;">System Status</div>
        <div style="display: flex; flex-direction: column; gap: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; color: #334155;">
                <span>AI Service (Gemini)</span>
                {get_dot(ai_ready)}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; color: #334155;">
                <span>Whisper Engine</span>
                {get_dot(whisper_ready)}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; color: #334155;">
                <span>SQLite Database</span>
                {get_dot(db_ready)}
            </div>
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_hero_banner(title: str, subtitle: str, badge_text: str = "AI-Powered Intelligence"):
    """Render eye-catching SaaS hero card."""
    html = f"""
    <div class="hero-banner">
        <div class="hero-badge">✨ {badge_text}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-desc">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_card(title: str, value: Any, subtitle: str = "", icon: str = "📊", icon_bg: str = "#eef2ff"):
    """Render clean metric card container."""
    html = f"""
    <div class="metric-card">
        <div class="metric-header">
            <span class="metric-label">{title}</span>
            <div class="metric-icon-box" style="background: {icon_bg};">{icon}</div>
        </div>
        <div class="metric-val">{value}</div>
        <div class="metric-sub">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_step_indicator(steps: List[str], current_step: int):
    """Render visual 4-step pipeline progress stepper."""
    items_html = []
    for i, step_name in enumerate(steps, 1):
        if i < current_step:
            cls = "done"
            icon = "✓"
        elif i == current_step:
            cls = "active"
            icon = f"0{i}"
        else:
            cls = "inactive"
            icon = f"0{i}"
        
        items_html.append(f"""
            <div class="step-item">
                <div class="step-num {cls}">{icon}</div>
                <span class="step-text" style="color: {'#0f172a' if i <= current_step else '#94a3b8'};">{step_name}</span>
            </div>
        """)
        if i < len(steps):
            items_html.append('<div class="step-divider"></div>')

    html = f"""
    <div class="step-wrapper">
        {''.join(items_html)}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(title: str, description: str, icon: str = "📂"):
    """Render polished empty state with icon and descriptive text."""
    html = f"""
    <div class="empty-state-box">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Return HTML for task status badge."""
    stat = (status or "Pending").strip().title()
    if stat == "Completed":
        return '<span class="pill-badge badge-completed">✅ Completed</span>'
    elif stat == "In Progress":
        return '<span class="pill-badge badge-progress">🚧 In Progress</span>'
    elif stat == "Blocked":
        return '<span class="pill-badge badge-blocked">⛔ Blocked</span>'
    else:
        return '<span class="pill-badge badge-pending">⏳ Pending</span>'


def render_priority_badge(priority: Optional[str]) -> str:
    """Return HTML for task priority badge."""
    p = (priority or "Medium").strip().capitalize()
    if p == "High":
        return '<span class="pill-badge badge-high">🔥 High</span>'
    elif p == "Low":
        return '<span class="pill-badge badge-low">⚡ Low</span>'
    else:
        return '<span class="pill-badge badge-medium">📌 Medium</span>'


def render_footer():
    """Render subtle professional footer."""
    html = """
    <div class="app-footer">
        <div><strong>AI Career Intelligence Platform</strong> • AI-Powered Interview & Career Insights</div>
        <div>Milestone 2 • Production Ready</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
