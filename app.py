import streamlit as st
import pytz
from datetime import datetime

st.set_page_config(
    page_title="AI Trading Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

if 'scanner_running' not in st.session_state:
    st.session_state.scanner_running = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_dashboard()

def show_login_page():
    st.markdown("""
    <div style='text-align:center; padding:50px'>
        <h1 style='color:#00FF88'>📈 AI Trading Scanner</h1>
        <p style='color:#AAAAAA'>Professional Forex & Indices Scanner</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if email and password:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Please enter email and password!")
        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass")
            if st.button("Sign Up", use_container_width=True):
                if new_email and new_pass and confirm_pass:
                    if new_pass == confirm_pass:
                        st.success("Account created! Please login.")
                    else:
                        st.error("Passwords do not match!")
                else:
                    st.error("Please fill all fields!")

def show_dashboard():
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center'>
            <h2 style='color:#00FF88'>📈 Trading Scanner</h2>
            <p style='color:#AAAAAA'>Welcome, {st.session_state.user_email}</p>
            <p style='color:#AAAAAA'>{get_ist_time().strftime('%d %b %Y %H:%M:%S IST')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "📊 Active Signals",
            "📰 News",
            "📓 Trade Journal",
            "📅 Calendar",
            "📈 Performance",
            "⚙️ Settings"
        ])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.scanner_running = False
            st.rerun()

    if page == "🏠 Dashboard":
        show_main_dashboard()
    elif page == "📊 Active Signals":
        st.title("📊 Active Signals")
        st.info("Scanner must be running to see signals!")
    elif page == "📰 News":
        st.title("📰 Market News")
        st.info("News engine coming soon!")
    elif page == "📓 Trade Journal":
        st.title("📓 Trade Journal")
        st.info("Journal coming soon!")
    elif page == "📅 Calendar":
        st.title("📅 Calendar Analytics")
        st.info("Calendar coming soon!")
    elif page == "📈 Performance":
        st.title("📈 Performance Stats")
        st.info("Performance engine coming soon!")
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        st.info("Settings coming soon!")

def show_main_dashboard():
    st.title("🏠 Dashboard")
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if not st.session_state.scanner_running:
            st.markdown("""
            <div style='text-align:center'>
                <div style='width:150px;height:150px;
                border-radius:50%;
                background:radial-gradient(circle,#003300,#00FF88);
                border:3px solid #00FF88;margin:auto;
                box-shadow:0 0 30px #00FF88;
                display:flex;align-items:center;
                justify-content:center;
                font-size:1.5em;color:white;
                font-weight:bold;'>START</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶ START SCANNER",
                use_container_width=True,
                type="primary"):
                st.session_state.scanner_running = True
                st.rerun()
        else:
            st.markdown("""
            <div style='text-align:center'>
                <div style='width:150px;height:150px;
                border-radius:50%;
                background:radial-gradient(circle,#330000,#FF4444);
                border:3px solid #FF4444;margin:auto;
                box-shadow:0 0 30px #FF4444;
                display:flex;align-items:center;
                justify-content:center;
                font-size:1.5em;color:white;
                font-weight:bold;'>STOP</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⏹ STOP SCANNER",
                use_container_width=True):
                st.session_state.scanner_running = False
                st.rerun()
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = "🟢 ACTIVE" if st.session_state.scanner_running else "🔴 STOPPED"
        st.metric("Scanner Status", status)
    with col2:
        st.metric("Active Signals", "0")
    with col3:
        st.metric("Today's Alerts", "0")
    with col4:
        st.metric("Win Rate", "0%")
    st.divider()
    st.subheader("📡 Pairs Being Scanned")
    pairs = ["XAUUSD","USDJPY","AUDCAD","GBPJPY",
             "GBPUSD","EURUSD","EURJPY","US30","NAS100"]
    cols = st.columns(3)
    for i, pair in enumerate(pairs):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:#1A1A2E;padding:10px;
            border-radius:8px;text-align:center;
            margin:5px;border:1px solid #00FF88'>
                <b style='color:#00FF88'>{pair}</b><br>
                <small style='color:#AAAAAA'>Scanning...</small>
            </div>
