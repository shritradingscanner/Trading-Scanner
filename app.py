import streamlit as st
import pytz
import requests
from datetime import datetime
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="AI Trading Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

def send_discord_alert(message):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        payload = {"content": message}
        requests.post(webhook_url, json=payload)
        return True
    except:
        return False

def get_market_data(symbol, period="1d", interval="5m"):
    try:
        ticker_map = {
            "XAUUSD": "GC=F",
            "USDJPY": "JPY=X",
            "AUDCAD": "AUDCAD=X",
            "GBPJPY": "GBPJPY=X",
            "GBPUSD": "GBPUSD=X",
            "EURUSD": "EURUSD=X",
            "EURJPY": "EURJPY=X",
            "US30": "YM=F",
            "NAS100": "NQ=F"
        }
        ticker = ticker_map.get(symbol, symbol)
        data = yf.download(ticker, period=period,
            interval=interval, progress=False)
        return data
    except:
        return None

def calculate_rsi(data, period=14):
    try:
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except:
        return None

def calculate_confidence(data, symbol):
    score = 0
    reasons = []

    try:
        close = data['Close'].iloc[-1]
        open_price = data['Open'].iloc[-1]
        high = data['High'].iloc[-1]
        low = data['Low'].iloc[-1]

        ma20 = data['Close'].rolling(20).mean().iloc[-1]
        ma50 = data['Close'].rolling(50).mean().iloc[-1]
        rsi = calculate_rsi(data)

        if close > ma20:
            score += 20
            reasons.append("Price above MA20")
        if ma20 > ma50:
            score += 20
            reasons.append("Bullish MA Cross")
        if rsi and rsi < 70 and rsi > 30:
            score += 20
            reasons.append("RSI in valid zone")
        if close > open_price:
            score += 20
            reasons.append("Bullish candle")
        if (high - low) > 0:
            score += 20
            reasons.append("Valid price range")

        direction = "BUY" if close > ma20 else "SELL"
        entry = float(close)
        sl = entry - (high - low) if direction == "BUY" else entry + (high - low)
        tp = entry + 2 * (high - low) if direction == "BUY" else entry - 2 * (high - low)

        return {
            "score": score,
            "direction": direction,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp": round(tp, 5),
            "rr": "1:2",
            "reasons": reasons
        }
    except:
        return None

if 'scanner_running' not in st.session_state:
    st.session_state.scanner_running = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'alerts_sent' not in st.session_state:
    st.session_state.alerts_sent = 0

def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_dashboard()

def show_login_page():
    st.title("📈 AI Trading Scanner")
    st.subheader("Professional Forex and Indices Scanner")
    st.divider()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input(
                "Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if email and password:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Please enter email and password!")
        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_pass = st.text_input(
                "Password", type="password", key="signup_pass")
            confirm_pass = st.text_input(
                "Confirm Password", type="password",
                key="confirm_pass")
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
        st.title("📈 Trading Scanner")
        st.write("Welcome, " + str(st.session_state.user_email))
        st.write(get_ist_time().strftime('%d %b %Y %H:%M:%S IST'))
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
        show_signals_page()
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
        show_settings_page()

def show_main_dashboard():
    st.title("🏠 Dashboard")
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if not st.session_state.scanner_running:
            st.success("Scanner is STOPPED")
            if st.button("▶ START SCANNER",
                use_container_width=True,
                type="primary"):
                st.session_state.scanner_running = True
                send_discord_alert(
                    "🟢 AI Trading Scanner STARTED!\n" +
                    "Scanning: XAUUSD, EURUSD, GBPUSD, " +
                    "USDJPY, GBPJPY, EURJPY, " +
                    "AUDCAD, US30, NAS100")
                st.rerun()
        else:
            st.error("Scanner is ACTIVE")
            if st.button("⏹ STOP SCANNER",
                use_container_width=True):
                st.session_state.scanner_running = False
                send_discord_alert(
                    "🔴 AI Trading Scanner STOPPED!")
                st.rerun()

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.session_state.scanner_running:
            st.metric("Scanner", "🟢 ACTIVE")
        else:
            st.metric("Scanner", "🔴 STOPPED")
    with col2:
        st.metric("Signals", len(st.session_state.signals))
    with col3:
        st.metric("Alerts Sent", st.session_state.alerts_sent)
    with col4:
        st.metric("Win Rate", "0%")

    st.divider()

    if st.session_state.scanner_running:
        st.subheader("📡 Live Scanner Running...")
        pairs = ["XAUUSD","USDJPY","AUDCAD","GBPJPY",
                 "GBPUSD","EURUSD","EURJPY","US30","NAS100"]

        if st.button("🔄 Scan Now", type="primary"):
            with st.spinner("Scanning all pairs..."):
                new_signals = []
                for pair in pairs:
                    data = get_market_data(pair)
                    if data is not None and len(data) > 50:
                        result = calculate_confidence(data, pair)
                        if result:
                            result['pair'] = pair
                            result['time'] = get_ist_time().strftime(
                                '%H:%M:%S IST')
                            new_signals.append(result)
                            if result['score'] >= 80:
                                msg = (
                                    f"🚨 HIGH CONFIDENCE SIGNAL!\n\n"
                                    f"Pair: {pair}\n"
                                    f"Direction: {result['direction']}\n"
                                    f"Confidence: {result['score']}%\n"
                                    f"Entry: {result['entry']}\n"
                                    f"SL: {result['sl']}\n"
                                    f"TP: {result['tp']}\n"
                                    f"RR: {result['rr']}\n"
                                    f"Reasons: {', '.join(result['reasons'])}\n"
                                    f"Time: {result['time']}"
                                )
                                send_discord_alert(msg)
                                st.session_state.alerts_sent += 1

                st.session_state.signals = new_signals
                st.success("Scan complete! " +
                    str(len(new_signals)) + " pairs analyzed!")
                st.rerun()

    st.subheader("📡 Pairs Being Scanned")
    pairs = ["XAUUSD","USDJPY","AUDCAD","GBPJPY",
             "GBPUSD","EURUSD","EURJPY","US30","NAS100"]
    cols = st.columns(3)
    for i, pair in enumerate(pairs):
        with cols[i % 3]:
            st.info(pair + " - Ready")

def show_signals_page():
    st.title("📊 Active Signals")
    if not st.session_state.signals:
        st.info("No signals yet! Go to Dashboard and click Scan Now!")
        return
    for signal in st.session_state.signals:
        if signal['score'] >= 80:
            color = "🟢"
        elif signal['score'] >= 60:
            color = "🟡"
        else:
            color = "🔴"
        with st.expander(
            color + " " + signal['pair'] +
            " | " + signal['direction'] +
            " | Confidence: " + str(signal['score']) + "%"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Entry", signal['entry'])
            with col2:
                st.metric("Stop Loss", signal['sl'])
            with col3:
                st.metric("Take Profit", signal['tp'])
            st.write("RR Ratio: " + signal['rr'])
            st.write("Time: " + signal['time'])
            st.write("Reasons: " + ", ".join(signal['reasons']))

def show_settings_page():
    st.title("⚙️ Settings")
    st.subheader("Discord Settings")
    if st.button("Test Discord Alert"):
        success = send_discord_alert(
            "✅ Test alert from AI Trading Scanner!")
        if success:
            st.success("Discord alert sent successfully!")
        else:
            st.error("Discord alert failed! Check webhook URL!")

if __name__ == "__main__":
    main()
