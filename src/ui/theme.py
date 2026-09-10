"""
UI Theme and Design System for AI Career Intelligence Platform.
Defines color palette, typography, card elevation, badges, and Streamlit styling overrides.
"""

import streamlit as st


def apply_theme():
    """Inject modern SaaS CSS stylesheet into the Streamlit app."""
    css = """
    <style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --font-heading: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        
        --bg-main: #f8fafc;
        --bg-surface: #ffffff;
        --bg-subtle: #f1f5f9;
        
        --primary: #1e3a8a;
        --primary-light: #3b82f6;
        --primary-dark: #172554;
        --accent: #6366f1;
        --accent-gradient: linear-gradient(135deg, #1e3a8a 0%, #4f46e5 50%, #7c3aed 100%);
        --accent-subtle: #eef2ff;
        
        --text-main: #0f172a;
        --text-muted: #64748b;
        --text-subtle: #94a3b8;
        
        --border-color: #e2e8f0;
        --border-hover: #cbd5e1;
        
        --success: #10b981;
        --success-bg: #ecfdf5;
        --warning: #f59e0b;
        --warning-bg: #fffbeb;
        --danger: #ef4444;
        --danger-bg: #fef2f2;
        --info: #0ea5e9;
        --info-bg: #f0f9ff;
        
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.04);
        --radius: 12px;
        --radius-sm: 8px;
        --radius-lg: 16px;
    }

    /* Global Base Styling */
    html, body, [class*="css"] {
        font-family: var(--font-body) !important;
        color: var(--text-main);
        background-color: var(--bg-main);
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-heading) !important;
        color: var(--text-main);
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Streamlit Main Container Tweaks */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
        max-width: 1300px !important;
    }

    /* Hide standard Streamlit header & footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Sidebar Custom Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid var(--border-color) !important;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.02) !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.4rem !important;
        padding-left: 1.1rem !important;
        padding-right: 1.1rem !important;
    }

    /* Brand Logo Box in Sidebar */
    .sidebar-brand-box {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
        border: 1px solid #e0e7ff;
        border-radius: var(--radius);
        margin-bottom: 20px;
    }

    .brand-icon-circle {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: var(--accent-gradient);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);
    }

    .brand-text-title {
        font-family: var(--font-heading);
        font-weight: 800;
        font-size: 15px;
        color: #0f172a;
        line-height: 1.2;
    }

    .brand-text-sub {
        font-size: 10px;
        color: #6366f1;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Nav Item Styling */
    .nav-header {
        font-size: 11px;
        font-weight: 700;
        color: var(--text-subtle);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 16px 0 8px 6px;
    }

    /* Custom Modern Cards */
    .ui-card {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: var(--radius);
        padding: 20px 24px;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease-in-out;
        margin-bottom: 16px;
    }

    .ui-card:hover {
        border-color: var(--border-hover);
        box-shadow: var(--shadow-md);
    }

    /* Hero Banner Card */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #312e81 100%);
        border-radius: var(--radius-lg);
        padding: 30px 34px;
        color: #ffffff;
        box-shadow: var(--shadow-lg);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-banner::after {
        content: '';
        position: absolute;
        right: -30px;
        bottom: -30px;
        width: 220px;
        height: 220px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, rgba(99, 102, 241, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        color: #a5b4fc;
        margin-bottom: 14px;
    }

    .hero-title {
        font-family: var(--font-heading);
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }

    .hero-desc {
        font-size: 14px;
        color: #cbd5e1;
        max-width: 680px;
        line-height: 1.5;
        margin-bottom: 18px;
    }

    /* Metric Cards */
    .metric-card {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: var(--radius);
        padding: 16px 18px;
        box-shadow: var(--shadow-sm);
        display: flex;
        flex-direction: column;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: #cbd5e1;
    }

    .metric-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }

    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-icon-box {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }

    .metric-val {
        font-family: var(--font-heading);
        font-size: 26px;
        font-weight: 800;
        color: var(--text-main);
        line-height: 1;
        margin-bottom: 4px;
    }

    .metric-sub {
        font-size: 12px;
        color: var(--text-subtle);
    }

    /* Step Indicator */
    .step-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: var(--radius);
        padding: 14px 20px;
        margin-bottom: 24px;
    }

    .step-item {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .step-num {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
    }

    .step-num.active {
        background: var(--primary);
        color: #ffffff;
        box-shadow: 0 2px 6px rgba(30, 58, 138, 0.3);
    }

    .step-num.done {
        background: var(--success);
        color: #ffffff;
    }

    .step-num.inactive {
        background: #f1f5f9;
        color: var(--text-subtle);
    }

    .step-text {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-main);
    }

    .step-divider {
        flex: 1;
        height: 2px;
        background: #e2e8f0;
        margin: 0 16px;
    }

    /* Status & Priority Badges */
    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .badge-high {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
    }

    .badge-medium {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
    }

    .badge-low {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
    }

    .badge-pending {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }

    .badge-progress {
        background-color: #ede9fe;
        color: #6d28d9;
        border: 1px solid #ddd6fe;
    }

    .badge-completed {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }

    .badge-blocked {
        background-color: #fee2e2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }

    /* Empty States */
    .empty-state-box {
        text-align: center;
        padding: 42px 24px;
        background: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: var(--radius-lg);
        margin: 20px 0;
    }

    .empty-state-icon {
        font-size: 40px;
        margin-bottom: 10px;
        opacity: 0.85;
    }

    .empty-state-title {
        font-family: var(--font-heading);
        font-size: 17px;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 4px;
    }

    .empty-state-desc {
        font-size: 13.5px;
        color: var(--text-muted);
        max-width: 440px;
        margin: 0 auto 16px auto;
        line-height: 1.5;
    }

    /* Streamlit Button Overrides */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.1rem !important;
        transition: all 0.15s ease-in-out !important;
        border: 1px solid transparent !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--accent-gradient) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(79, 70, 229, 0.25) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35) !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
    }

    /* Streamlit Download Button */
    .stDownloadButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        background-color: #ffffff !important;
        color: var(--primary) !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stDownloadButton > button:hover {
        background-color: #f0f4ff !important;
        border-color: var(--primary-light) !important;
    }

    /* Streamlit Status / Expander */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
    }

    /* Footer Styling */
    .app-footer {
        margin-top: 48px;
        padding-top: 18px;
        border-top: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: var(--text-subtle);
        font-size: 12px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
