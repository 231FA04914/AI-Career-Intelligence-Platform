"""
User Authentication & Session Component (Milestone 4 - Task 1 & Task 7)
Provides a premium, full-page AI SaaS login & registration gateway with high-contrast, crystal-clear inputs and navigation.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from src.auth import AuthManager


def render_auth_sidebar_widget(auth_manager: AuthManager) -> Optional[Dict[str, Any]]:
    """
    Render user session info and login/logout controls in the sidebar.
    Returns the currently active user dictionary, or None if not logged in.
    """
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None

    current_user = st.session_state.get("auth_user")

    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="nav-header">Account & Security</div>', unsafe_allow_html=True)

    if current_user:
        uname = current_user.get("username", "User")
        role = current_user.get("role", "user")
        profile_html = f"""
<div style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); padding: 12px 14px; border-radius: 10px; border: 1px solid rgba(99, 102, 241, 0.3); margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
        <div style="width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #a855f7); display: flex; align-items: center; justify-content: center; font-size: 14px; color: white;">👤</div>
        <div>
            <div style="font-weight: 700; font-size: 13.5px; color: #f8fafc;">{uname}</div>
            <div style="font-size: 11px; color: #94a3b8;">Role: <span style="background: rgba(99, 102, 241, 0.25); color: #c7d2fe; padding: 1px 6px; border-radius: 4px; font-weight: 600; font-size: 10.5px;">{role.upper()}</span></div>
        </div>
    </div>
</div>
"""
        st.sidebar.markdown(profile_html.strip(), unsafe_allow_html=True)

        col_l1, col_l2 = st.sidebar.columns(2)
        with col_l1:
            if st.button("🚪 Logout", key="btn_auth_logout", use_container_width=True):
                st.session_state["auth_user"] = None
                st.session_state["nav_page"] = "Dashboard"
                st.rerun()
        with col_l2:
            if st.button("🔄 Switch", key="btn_auth_switch", use_container_width=True):
                st.session_state["show_auth_modal"] = True
                st.rerun()
    else:
        st.sidebar.warning("⚠️ Authentication Required")
        if st.sidebar.button("🔐 Sign In / Register", key="btn_sidebar_login", type="primary", use_container_width=True):
            st.session_state["show_auth_modal"] = True
            st.rerun()

    return current_user


def render_auth_dialog(auth_manager: AuthManager):
    """
    Render login / registration modal dialog when switching accounts while logged in.
    """
    if not st.session_state.get("show_auth_modal", False):
        return

    st.markdown("### 🔐 User Authentication & Switch Account")
    tab_login, tab_register, tab_demo = st.tabs(["🔑 Login", "📝 Create Account", "⚡ Quick Demo Accounts"])

    with tab_login:
        with st.form("form_login_dialog"):
            l_user = st.text_input("Username or Email:")
            l_pass = st.text_input("Password:", type="password")
            l_submit = st.form_submit_button("Sign In", type="primary")

            if l_submit:
                user = auth_manager.authenticate_user(l_user, l_pass)
                if user:
                    st.session_state["auth_user"] = user
                    st.session_state["show_auth_modal"] = False
                    st.session_state["nav_page"] = "Dashboard"
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab_register:
        with st.form("form_register_dialog"):
            r_user = st.text_input("Choose Username:")
            r_email = st.text_input("Email Address:")
            r_pass = st.text_input("Password (min 6 chars):", type="password")
            r_role = st.selectbox("Account Role:", ["user", "admin"])
            r_submit = st.form_submit_button("Create Account", type="primary")

            if r_submit:
                try:
                    user = auth_manager.register_user(r_user, r_email, r_pass, role=r_role)
                    st.session_state["auth_user"] = user
                    st.session_state["show_auth_modal"] = False
                    st.session_state["nav_page"] = "Dashboard"
                    st.success(f"Account created successfully for {r_user}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration error: {e}")

    with tab_demo:
        st.caption("One-click switch between demo user accounts to test multi-tenant access control:")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if st.button("👤 Demo Admin (demo_user)", key="btn_demo_admin_dialog", use_container_width=True):
                user = auth_manager.authenticate_user("demo_user", "DemoUser2026!")
                st.session_state["auth_user"] = user
                st.session_state["show_auth_modal"] = False
                st.session_state["nav_page"] = "Dashboard"
                st.rerun()
        with d_col2:
            if st.button("👤 Demo User 2 (user2)", key="btn_demo_user2_dialog", use_container_width=True):
                try:
                    auth_manager.register_user("user2", "user2@meetingintel.ai", "User2Password!", role="user")
                except Exception:
                    pass
                user = auth_manager.authenticate_user("user2", "User2Password!")
                st.session_state["auth_user"] = user
                st.session_state["show_auth_modal"] = False
                st.session_state["nav_page"] = "Dashboard"
                st.rerun()

    if st.button("✖️ Close", key="btn_close_auth_dialog"):
        st.session_state["show_auth_modal"] = False
        st.rerun()
    st.markdown("---")


def render_login_view(auth_manager: AuthManager):
    """
    Render full-page executive AI SaaS authentication portal with crystal-clear high-contrast styling.
    """
    # 1. Full-Page Immersive High-Contrast Styling
    css = """
<style>
/* Hide sidebar completely on login page */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Full Width & Background Canvas */
.stApp {
    background-color: #070B14 !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.18) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.18) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(30, 27, 75, 0.45) 0px, transparent 50%) !important;
    background-attachment: fixed !important;
    color: #F8FAFC !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

.block-container {
    max-width: 1360px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Header Brand Bar */
.saas-top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0 20px 0;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.saas-logo-box {
    display: flex;
    align-items: center;
    gap: 12px;
}

.saas-logo-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
    color: white;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.saas-logo-title {
    font-size: 19px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
}

.saas-logo-subtitle {
    font-size: 11px;
    font-weight: 600;
    color: #818cf8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.saas-status-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 11.5px;
    font-weight: 700;
    color: #34d399;
    letter-spacing: 0.04em;
}

.saas-status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
}

/* Left Hero Typography */
.hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(129, 140, 248, 0.35);
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 11.5px;
    font-weight: 700;
    color: #c7d2fe;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.hero-h1 {
    font-size: 38px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.03em;
    color: #FFFFFF;
    margin-bottom: 12px;
}

.hero-gradient-span {
    background: linear-gradient(135deg, #a5b4fc 0%, #c084fc 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-p {
    font-size: 15.5px;
    line-height: 1.5;
    color: #cbd5e1;
    margin-bottom: 24px;
    max-width: 520px;
}

/* Auth Glass Card */
.auth-panel {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 22px 24px;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
    margin-bottom: 18px;
}

/* Showcase Glass Card */
.showcase-panel {
    background: linear-gradient(145deg, rgba(24, 24, 47, 0.85) 0%, rgba(15, 23, 42, 0.92) 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 26px 28px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 30px rgba(99, 102, 241, 0.15);
}

.showcase-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.showcase-title {
    font-size: 17px;
    font-weight: 800;
    color: #FFFFFF;
}

.showcase-sub {
    font-size: 12px;
    color: #a5b4fc;
}

.showcase-chips {
    display: flex;
    gap: 6px;
}

.chip-tag {
    font-size: 10.5px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(129, 140, 248, 0.35);
    color: #c7d2fe;
}

.feature-card {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 13px 15px;
    margin-bottom: 11px;
    transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.feature-card:hover {
    background: rgba(99, 102, 241, 0.12);
    border-color: rgba(168, 85, 247, 0.45);
    transform: translateX(3px);
}

.feature-icon-circle {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    color: white;
    flex-shrink: 0;
    box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35);
}

.feature-text-h {
    font-size: 14px;
    font-weight: 700;
    color: #F1F5F9;
    margin-bottom: 2px;
}

.feature-text-d {
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.4;
}

.showcase-footer {
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
    color: #94a3b8;
}

/* ======================================================= */
/* CRITICAL FIXES: Tabs, Inputs, Placeholders, Labels       */
/* ======================================================= */

/* 1. Ultra High-Contrast Segmented Tabs */
div[data-testid="stTabs"] div[data-baseweb="tab-list"],
div[data-baseweb="tab-list"] {
    background: #0f172a !important;
    border: 1.5px solid #334155 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 8px !important;
    margin-bottom: 20px !important;
}

div[data-baseweb="tab-list"] button[data-baseweb="tab"],
button[role="tab"] {
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    color: #cbd5e1 !important;
    font-size: 14.5px !important;
    font-weight: 700 !important;
    transition: all 0.2s ease !important;
}

div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover,
button[role="tab"]:hover {
    color: #ffffff !important;
    background: rgba(255, 255, 255, 0.08) !important;
}

div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"],
button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.45) !important;
}

div[data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"] {
    display: none !important;
}

/* 2. High-Contrast White Inputs with Pure Black Text */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-testid="stTextInput"] div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.35) !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input,
div[data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    color: #000000 !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    padding: 10px 14px !important;
    caret-color: #000000 !important;
}

div[data-baseweb="input"] input::placeholder,
div[data-testid="stTextInput"] input::placeholder {
    color: #64748b !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
}

/* 3. High-Contrast Form Labels */
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stCheckbox"] label {
    color: #f8fafc !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    margin-bottom: 4px !important;
}

div[data-testid="stCheckbox"] label p {
    color: #f1f5f9 !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
}

/* 4. High-Contrast Selectbox with Black Text */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #000000 !important;
    font-weight: 700 !important;
}

div[data-baseweb="select"] div[aria-selected="true"],
div[data-baseweb="select"] span,
div[data-baseweb="select"] * {
    color: #000000 !important;
    font-weight: 700 !important;
}

/* 5. High-Impact Submit Button */
div[data-testid="stFormSubmitButton"] > button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #4f46e5 100%) !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7rem 1.4rem !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

div[data-testid="stFormSubmitButton"] > button:hover,
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(139, 92, 246, 0.55) !important;
}

/* 6. Secondary Buttons */
.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(99, 102, 241, 0.2) !important;
    border-color: rgba(129, 140, 248, 0.4) !important;
    color: #ffffff !important;
}

/* 7. Sandbox Box */
.sandbox-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px 16px;
    margin-top: 14px;
}
</style>
"""
    st.markdown(css.strip(), unsafe_allow_html=True)

    # 2. Header Top Bar
    top_bar_html = """
<div class="saas-top-bar">
    <div class="saas-logo-box">
        <div class="saas-logo-icon">🎙️</div>
        <div>
            <div class="saas-logo-title">AI Career Intelligence</div>
            <div class="saas-logo-subtitle">Executive Speech & RAG Platform</div>
        </div>
    </div>
    <div class="saas-status-pill">
        <span class="saas-status-dot"></span>
        <span>SYSTEM ACTIVE • v4.0</span>
    </div>
</div>
"""
    st.markdown(top_bar_html.strip(), unsafe_allow_html=True)

    # 3. Two-Column Layout
    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    with col_left:
        # Welcome Hero Copy
        left_hero_html = """
<div class="hero-tag">✨ Next-Gen AI Career Platform</div>
<h1 class="hero-h1">Your Career Intelligence <span class="hero-gradient-span">Starts Here.</span></h1>
<p class="hero-p">Turn interviews, conversations, and career insights into actionable intelligence with AI.</p>
"""
        st.markdown(left_hero_html.strip(), unsafe_allow_html=True)

        if st.session_state.get("reg_success_msg"):
            st.success(st.session_state["reg_success_msg"])

        # Mode Switcher Tabs
        tab_signin, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with tab_signin:
            prefill_user = st.session_state.get("registered_username_hint", "")

            # Saved Accounts Helper
            try:
                registered_list = auth_manager.list_registered_users()
                user_choices = [u["username"] for u in registered_list if u.get("username")]
            except Exception:
                user_choices = []

            if user_choices:
                with st.expander("👥 Saved Accounts On This System", expanded=False):
                    st.caption("Select a registered profile to prefill the login field:")
                    sel_acc = st.selectbox(
                        "Registered Profiles:",
                        options=["(Select account)"] + user_choices,
                        key="sel_known_profile_opt"
                    )
                    if sel_acc and sel_acc != "(Select account)":
                        prefill_user = sel_acc

            with st.form("form_signin_modern"):
                username_or_email = st.text_input(
                    "Username or Email Address:",
                    value=prefill_user,
                    placeholder="e.g. demo_user or your_username"
                )

                show_pw = st.checkbox("👁️ Show password", key="chk_show_pw_modern")
                pw_type = "default" if show_pw else "password"
                password = st.text_input(
                    "Password:",
                    type=pw_type,
                    placeholder="Enter your password"
                )

                btn_signin = st.form_submit_button(
                    "🚀 Sign In to Dashboard",
                    type="primary",
                    use_container_width=True
                )

                if btn_signin:
                    if not username_or_email or not password:
                        st.error("Please enter both username/email and password.")
                    else:
                        user = auth_manager.authenticate_user(username_or_email, password)
                        if user:
                            st.session_state["auth_user"] = user
                            st.session_state["show_auth_modal"] = False
                            st.session_state["nav_page"] = "Dashboard"
                            st.session_state.pop("reg_success_msg", None)
                            st.success(f"Welcome back, {user['username']}! Redirecting to Dashboard...")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please verify your username/email and password.")

        with tab_signup:
            st.caption("Register a new persistent account. Saved securely to the database so you can sign in directly anytime.")
            with st.form("form_signup_modern"):
                reg_username = st.text_input("Choose Username:", placeholder="e.g. alex_smith")
                reg_email = st.text_input("Email Address:", placeholder="e.g. alex@company.com")

                show_pw_r = st.checkbox("👁️ Show password", key="chk_show_pw_reg_mod")
                pw_type_r = "default" if show_pw_r else "password"
                reg_password = st.text_input(
                    "Password (min 6 characters):",
                    type=pw_type_r,
                    placeholder="Create strong password"
                )

                reg_role = st.selectbox(
                    "Account Role:",
                    ["user", "admin"],
                    help="Admins can inspect system logs; standard users have private tenant workspaces."
                )

                btn_register = st.form_submit_button(
                    "✨ Create My Account",
                    type="primary",
                    use_container_width=True
                )

                if btn_register:
                    if not reg_username or not reg_email or not reg_password:
                        st.error("Please fill in all registration fields.")
                    else:
                        try:
                            user = auth_manager.register_user(reg_username, reg_email, reg_password, role=reg_role)
                            st.session_state["registered_username_hint"] = reg_username
                            st.session_state["reg_success_msg"] = f"🎉 Account '{reg_username}' created! Switch to the 'Sign In' tab to log in."
                            st.success(f"🎉 Account '{reg_username}' registered successfully! Switch to **Sign In** to continue.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Registration error: {e}")

        # Quick Demo Access
        demo_header_html = """
<div class="sandbox-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <div style="font-weight: 700; font-size: 13px; color: #e2e8f0;">⚡ Quick Demo Sandbox (Multi-Tenant)</div>
        <span style="font-size: 10.5px; color: #818cf8; background: rgba(99, 102, 241, 0.15); padding: 2px 7px; border-radius: 4px; font-weight: 600;">1-Click Evaluation</span>
    </div>
    <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">Select a pre-populated test profile to evaluate features instantly:</div>
</div>
"""
        st.markdown(demo_header_html.strip(), unsafe_allow_html=True)

        d1, d2 = st.columns(2)
        with d1:
            if st.button("👑 Demo Admin (demo_user)", key="btn_quick_admin_v4", use_container_width=True):
                user = auth_manager.authenticate_user("demo_user", "DemoUser2026!")
                if user:
                    st.session_state["auth_user"] = user
                    st.session_state["show_auth_modal"] = False
                    st.session_state["nav_page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("Could not sign in with demo_user credentials.")
        with d2:
            if st.button("👤 Demo User 2 (user2)", key="btn_quick_user2_v4", use_container_width=True):
                try:
                    auth_manager.register_user("user2", "user2@meetingintel.ai", "User2Password!", role="user")
                except Exception:
                    pass
                user = auth_manager.authenticate_user("user2", "User2Password!")
                if user:
                    st.session_state["auth_user"] = user
                    st.session_state["show_auth_modal"] = False
                    st.session_state["nav_page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("Could not sign in with user2 credentials.")

    with col_right:
        # Showcase Panel & 4 Feature Highlights
        showcase_html = """
<div class="showcase-panel">
    <div class="showcase-header">
        <div>
            <div class="showcase-title">🧠 AI Career Engine</div>
            <div class="showcase-sub">Autonomous Speech & RAG Intelligence</div>
        </div>
        <div class="showcase-chips">
            <span class="chip-tag">Whisper ASR</span>
            <span class="chip-tag">Gemini LLM</span>
            <span class="chip-tag">Vector DB</span>
        </div>
    </div>
    <div class="feature-card">
        <div class="feature-icon-circle">🎙️</div>
        <div>
            <div class="feature-text-h">AI-Powered Interview Analysis</div>
            <div class="feature-text-d">Deep speech-to-text with Whisper, behavioral tone insights, filler-word diagnostics, and speaker diarization.</div>
        </div>
    </div>
    <div class="feature-card">
        <div class="feature-icon-circle">📋</div>
        <div>
            <div class="feature-text-h">Intelligent Meeting Summaries</div>
            <div class="feature-text-d">Instant executive briefs, high-priority action items with owner tracking, and decision matrix extraction.</div>
        </div>
    </div>
    <div class="feature-card">
        <div class="feature-icon-circle">🔍</div>
        <div>
            <div class="feature-text-h">Semantic Search & RAG Assistant</div>
            <div class="feature-text-d">Vector embeddings across all conversation archives with an AI assistant for deep contextual Q&A.</div>
        </div>
    </div>
    <div class="feature-card">
        <div class="feature-icon-circle">📊</div>
        <div>
            <div class="feature-text-h">Career Insights & Skill Intelligence</div>
            <div class="feature-text-d">Automated competency scoring, career trajectory recommendations, and interview readiness rubrics.</div>
        </div>
    </div>
    <div class="showcase-footer">
        <span>🔒 Multi-Tenant Data Isolation</span>
        <span>🛡️ Cryptographic HMAC Session Tokens</span>
    </div>
</div>
"""
        st.markdown(showcase_html.strip(), unsafe_allow_html=True)
