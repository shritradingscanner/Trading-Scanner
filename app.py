import streamlit as st
import pytz
import requests
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np

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
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    except Exception:
        return False

TICKER_MAP = {
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

TWELVE_MAP = {
    "XAUUSD": "XAU/USD",
    "USDJPY": "USD/JPY",
    "AUDCAD": "AUD/CAD",
    "GBPJPY": "GBP/JPY",
    "GBPUSD": "GBP/USD",
    "EURUSD": "EUR/USD",
    "EURJPY": "EUR/JPY",
    "US30": "US30/USD",
    "NAS100": "IXIC"
}

def get_data_twelvedata(symbol, interval="5min"):
    try:
        api_key = st.secrets["TWELVEDATA_KEY"]
        td_symbol = TWELVE_MAP.get(symbol, symbol)
        url = (
            "https://api.twelvedata.com/time_series?"
            "symbol=" + td_symbol +
            "&interval=" + interval +
            "&outputsize=100" +
            "&apikey=" + api_key
        )
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" not in data:
            return None
        values = data["values"]
        df = pd.DataFrame(values)
        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        })
        for col in ['Open','High','Low','Close']:
            df[col] = pd.to_numeric(
                df[col], errors='coerce')
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    except Exception:
        return None

def get_data_yfinance(symbol, interval="5m"):
    try:
        ticker = TICKER_MAP.get(symbol, symbol)
        df = yf.download(ticker, interval=interval,
            period="5d", progress=False)
        if df is not None and len(df) > 10:
            df.columns = ['Open','High','Low',
                'Close','Volume']
            df = df.reset_index(drop=True)
            return df
        return None
    except Exception:
        return None

def get_data(symbol, interval="5m"):
    interval_map = {
        "5m": "5min",
        "15m": "15min",
        "1h": "1h",
        "4h": "4h"
    }
    td_interval = interval_map.get(interval, "5min")
    df = get_data_twelvedata(symbol, td_interval)
    if df is not None and len(df) > 20:
        return df
    df = get_data_yfinance(symbol, interval)
    return df

def detect_bos(df):
    try:
        highs = df['High'].values
        lows = df['Low'].values
        current_close = float(df['Close'].values[-1])
        prev_high = float(max(highs[-40:-20]))
        prev_low = float(min(lows[-40:-20]))
        bullish_bos = current_close > prev_high
        bearish_bos = current_close < prev_low
        return bullish_bos, bearish_bos
    except Exception:
        return False, False

def detect_fvg(df):
    try:
        bullish_fvg = False
        bearish_fvg = False
        for i in range(2, min(20, len(df)-1)):
            high_before = float(df['High'].values[-i-1])
            low_after = float(df['Low'].values[-i+1])
            low_before = float(df['Low'].values[-i-1])
            high_after = float(df['High'].values[-i+1])
            if low_after > high_before:
                bullish_fvg = True
            if high_after < low_before:
                bearish_fvg = True
        return bullish_fvg, bearish_fvg
    except Exception:
        return False, False

def detect_liquidity_sweep(df):
    try:
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        recent_high = float(max(highs[-30:-5]))
        recent_low = float(min(lows[-30:-5]))
        current_high = float(highs[-1])
        current_low = float(lows[-1])
        current_close = float(closes[-1])
        bullish_sweep = (current_low < recent_low
            and current_close > recent_low)
        bearish_sweep = (current_high > recent_high
            and current_close < recent_high)
        return bullish_sweep, bearish_sweep
    except Exception:
        return False, False

def detect_choch(df):
    try:
        closes = df['Close'].values
        mid = len(closes) // 2
        first_trend = (float(closes[mid]) -
            float(closes[0]))
        second_trend = (float(closes[-1]) -
            float(closes[mid]))
        choch_bull = (first_trend < 0
            and second_trend > 0)
        choch_bear = (first_trend > 0
            and second_trend < 0)
        return choch_bull, choch_bear
    except Exception:
        return False, False

def calculate_rsi(df, period=14):
    try:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except Exception:
        return 50

def get_htf_bias(symbol):
    try:
        df_1h = get_data(symbol, interval="1h")
        if df_1h is None or len(df_1h) < 50:
            return "NEUTRAL"
        ma20 = float(
            df_1h['Close'].rolling(20).mean().iloc[-1])
        ma50 = float(
            df_1h['Close'].rolling(50).mean().iloc[-1])
        current = float(df_1h['Close'].iloc[-1])
        if current > ma20 and ma20 > ma50:
            return "BULLISH"
        elif current < ma20 and ma20 < ma50:
            return "BEARISH"
        return "NEUTRAL"
    except Exception:
        return "NEUTRAL"

def detect_market_regime(df):
    try:
        closes = df['Close'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        atr = float(np.mean(highs[-14:] - lows[-14:]))
        ma20 = float(np.mean(closes[-20:]))
        deviation = float(np.std(closes[-20:]))
        price_range = float(
            max(closes[-20:]) - min(closes[-20:]))
        if atr > deviation * 1.5:
            return "VOLATILE"
        elif price_range < atr * 3:
            return "RANGING"
        elif closes[-1] > ma20:
            return "TRENDING UP"
        else:
            return "TRENDING DOWN"
    except Exception:
        return "UNKNOWN"

def analyze_pair(symbol):
    try:
        df_5m = get_data(symbol, interval="5m")
        if df_5m is None or len(df_5m) < 50:
            return None

        score = 0
        reasons = []
        negative_reasons = []

        htf_bias = get_htf_bias(symbol)
        regime = detect_market_regime(df_5m)

        bull_bos, bear_bos = detect_bos(df_5m)
        bull_fvg, bear_fvg = detect_fvg(df_5m)
        bull_sweep, bear_sweep = detect_liquidity_sweep(
            df_5m)
        bull_choch, bear_choch = detect_choch(df_5m)
        rsi = calculate_rsi(df_5m)

        close = float(df_5m['Close'].iloc[-1])
        highs = df_5m['High'].values.astype(float)
        lows = df_5m['Low'].values.astype(float)
        atr = float(np.mean(highs[-14:] - lows[-14:]))

        is_bullish = (bull_bos or bull_fvg
            or bull_sweep or bull_choch)
        is_bearish = (bear_bos or bear_fvg
            or bear_sweep or bear_choch)

        if is_bullish and not is_bearish:
            direction = "BUY"
        elif is_bearish and not is_bullish:
            direction = "SELL"
        elif is_bullish and is_bearish:
            if htf_bias == "BULLISH":
                direction = "BUY"
            elif htf_bias == "BEARISH":
                direction = "SELL"
            else:
                direction = "BUY"
        else:
            return None

        if htf_bias == "BULLISH" and direction == "BUY":
            score += 20
            reasons.append("HTF Bullish Alignment")
        elif htf_bias == "BEARISH" and direction == "SELL":
            score += 20
            reasons.append("HTF Bearish Alignment")
        elif htf_bias == "NEUTRAL":
            score += 10
            reasons.append("HTF Neutral")
        else:
            negative_reasons.append("HTF Conflict")

        if bull_bos and direction == "BUY":
            score += 25
            reasons.append("Bullish BOS")
        if bear_bos and direction == "SELL":
            score += 25
            reasons.append("Bearish BOS")
        if bull_fvg and direction == "BUY":
            score += 20
            reasons.append("Bullish FVG")
        if bear_fvg and direction == "SELL":
            score += 20
            reasons.append("Bearish FVG")
        if bull_sweep and direction == "BUY":
            score += 25
            reasons.append("Bullish Liquidity Sweep")
        if bear_sweep and direction == "SELL":
            score += 25
            reasons.append("Bearish Liquidity Sweep")
        if bull_choch and direction == "BUY":
            score += 20
            reasons.append("Bullish CHOCH")
        if bear_choch and direction == "SELL":
            score += 20
            reasons.append("Bearish CHOCH")

        if direction == "BUY" and 30 < rsi < 60:
            score += 10
            reasons.append("RSI Valid Zone")
        elif direction == "SELL" and 40 < rsi < 70:
            score += 10
            reasons.append("RSI Valid Zone")
        elif rsi > 80 or rsi < 20:
            negative_reasons.append("RSI Extreme")

        if direction == "BUY":
            entry = close
            sl = close - (atr * 1.5)
            tp = close + (atr * 3)
        else:
            entry = close
            sl = close + (atr * 1.5)
            tp = close - (atr * 3)

        rr = (abs(tp - entry) / abs(sl - entry)
            if abs(sl - entry) > 0 else 2.0)

        return {
            "pair": symbol,
            "direction": direction,
            "score": min(score, 100),
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp": round(tp, 5),
            "rr": round(rr, 2),
            "rsi": round(rsi, 1),
            "htf_bias": htf_bias,
            "regime": regime,
            "reasons": reasons,
            "negative": negative_reasons,
            "time": get_ist_time().strftime(
                '%d %b %Y %H:%M IST')
        }
    except Exception:
        return None

def format_discord_message(signal):
    grade = ("A+" if signal['score'] >= 90 else
             "A" if signal['score'] >= 80 else
             "B" if signal['score'] >= 70 else "C")
    emoji = ("🟢 BUY" if signal['direction'] == "BUY"
             else "🔴 SELL")
    reasons_text = "\n".join(
        ["✅ " + r for r in signal['reasons']])
    neg_text = "\n".join(
        ["❌ " + n for n in signal['negative']])
    msg = (
        "🚨 **HIGH CONFIDENCE SIGNAL** 🚨\n\n"
        "**" + emoji + " " + signal['pair'] + "**\n\n"
        "📊 Confidence: " + str(signal['score']) + "%\n"
        "🏆 Grade: " + grade + "\n\n"
        "💰 Entry: " + str(signal['entry']) + "\n"
        "🛑 Stop Loss: " + str(signal['sl']) + "\n"
        "🎯 Take Profit: " + str(signal['tp']) + "\n"
        "⚖️ RR Ratio: 1:" + str(signal['rr']) + "\n\n"
        "📈 HTF Bias: " + signal['htf_bias'] + "\n"
        "🌍 Market: " + signal['regime'] + "\n"
        "📉 RSI: " + str(signal['rsi']) + "\n\n"
        "✅ **Reasons:**\n" + reasons_text + "\n"
    )
    if signal['negative']:
        msg += "\n❌ **Caution:**\n" + neg_text + "\n"
    msg += "\n⏰ Time: " + signal['time']
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    return msg

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
if 'total_scans' not in st.session_state:
    st.session_state.total_scans = 0

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
            email = st.text_input("Email",
                key="login_email")
            password = st.text_input("Password",
                type="password", key="login_pass")
            if st.button("Login",
                use_container_width=True):
                if email and password:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error(
                        "Please enter email and password!")
        with tab2:
            new_email = st.text_input("Email",
                key="signup_email")
            new_pass = st.text_input("Password",
                type="password", key="signup_pass")
            confirm_pass = st.text_input(
                "Confirm Password",
                type="password", key="confirm_pass")
            if st.button("Sign Up",
                use_container_width=True):
                if new_email and new_pass and confirm_pass:
                    if new_pass == confirm_pass:
                        st.success(
                            "Account created! Please login.")
                    else:
                        st.error("Passwords do not match!")
                else:
                    st.error("Please fill all fields!")

def show_dashboard():
    with st.sidebar:
        st.title("📈 Trading Scanner")
        st.write("Welcome, " +
            str(st.session_state.user_email))
        st.write(get_ist_time().strftime(
            '%d %b %Y %H:%M:%S IST'))
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
        if st.button("🚪 Logout",
            use_container_width=True):
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
                    "🟢 **AI Trading Scanner STARTED!**\n"
                    "Scanning 9 pairs with SMC/ICT\n"
                    "Min confidence: 80%\n"
                    "Time: " + get_ist_time().strftime(
                        '%d %b %Y %H:%M IST'))
                st.rerun()
        else:
            st.error("Scanner is ACTIVE")
            if st.button("⏹ STOP SCANNER",
                use_container_width=True):
                st.session_state.scanner_running = False
                send_discord_alert(
                    "🔴 **AI Trading Scanner STOPPED!**\n"
                    "Total Scans: " +
                    str(st.session_state.total_scans) +
                    "\nAlerts Sent: " +
                    str(st.session_state.alerts_sent))
                st.rerun()

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.session_state.scanner_running:
            st.metric("Scanner", "🟢 ACTIVE")
        else:
            st.metric("Scanner", "🔴 STOPPED")
    with col2:
        st.metric("Signals",
            len(st.session_state.signals))
    with col3:
        st.metric("Alerts Sent",
            st.session_state.alerts_sent)
    with col4:
        st.metric("Total Scans",
            st.session_state.total_scans)

    st.divider()

    if st.session_state.scanner_running:
        st.subheader("📡 Scanner Active")
        if st.button("🔄 SCAN ALL PAIRS NOW",
            type="primary",
            use_container_width=True):
            pairs = [
                "XAUUSD","USDJPY","AUDCAD",
                "GBPJPY","GBPUSD","EURUSD",
                "EURJPY","US30","NAS100"
            ]
            progress = st.progress(0)
            status = st.empty()
            found_signals = []

            for idx, pair in enumerate(pairs):
                status.write("Analyzing " + pair + "...")
                progress.progress((idx+1)/len(pairs))
                result = analyze_pair(pair)
                if result:
                    found_signals.append(result)
                    if result['score'] >= 80:
                        msg = format_discord_message(result)
                        send_discord_alert(msg)
                        st.session_state.alerts_sent += 1

            st.session_state.signals = found_signals
            st.session_state.total_scans += 1
            progress.empty()
            status.empty()

            high_conf = [s for s in found_signals
                if s['score'] >= 80]
            st.success(
                "Scan Complete! Found " +
                str(len(found_signals)) +
                " setups. High Confidence (80%+): " +
                str(len(high_conf)))
            st.rerun()

    st.divider()
    st.subheader("📡 Pairs Being Scanned")
    pairs = [
        "XAUUSD","USDJPY","AUDCAD",
        "GBPJPY","GBPUSD","EURUSD",
        "EURJPY","US30","NAS100"
    ]
    cols = st.columns(3)
    for i, pair in enumerate(pairs):
        with cols[i % 3]:
            st.info(pair)

def show_signals_page():
    st.title("📊 Active Signals")
    if not st.session_state.signals:
        st.info(
            "No signals yet! Go to Dashboard "
            "and click Scan Now!")
        return

    high = [s for s in st.session_state.signals
        if s['score'] >= 80]
    medium = [s for s in st.session_state.signals
        if 60 <= s['score'] < 80]
    low = [s for s in st.session_state.signals
        if s['score'] < 60]

    if high:
        st.subheader("🟢 High Confidence (80%+)")
        for signal in high:
            with st.expander(
                "🟢 " + signal['pair'] + " " +
                signal['direction'] + " | " +
                str(signal['score']) + "% | " +
                signal['time']):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])
                st.write("RR: 1:" + str(signal['rr']))
                st.write("HTF: " + signal['htf_bias'])
                st.write("Market: " + signal['regime'])
                st.write("RSI: " + str(signal['rsi']))
                st.write("Reasons: " +
                    ", ".join(signal['reasons']))
                if signal['negative']:
                    st.warning("Caution: " +
                        ", ".join(signal['negative']))

    if medium:
        st.subheader("🟡 Medium Confidence (60-80%)")
        for signal in medium:
            with st.expander(
                "🟡 " + signal['pair'] + " " +
                signal['direction'] + " | " +
                str(signal['score']) + "%"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])
                st.write("RR: 1:" + str(signal['rr']))
                st.write("Reasons: " +
                    ", ".join(signal['reasons']))

    if low:
        st.subheader("🔴 Low Confidence")
        for signal in low:
            st.write("🔴 " + signal['pair'] +
                " | " + str(signal['score']) + "%")

def show_settings_page():
    st.title("⚙️ Settings")
    st.subheader("🔔 Discord Settings")
    if st.button("Test Discord Alert",
        use_container_width=True):
        success = send_discord_alert(
            "✅ **Test Alert from AI Trading Scanner!**\n"
            "Discord is working perfectly!\n"
            "Time: " + get_ist_time().strftime(
                '%d %b %Y %H:%M IST'))
        if success:
            st.success("Discord alert sent!")
        else:
            st.error(
                "Discord failed! Check webhook URL!")

    st.divider()
    st.subheader("📊 Scanner Info")
    st.info("Min Confidence: 80%")
    st.info("Pairs: XAUUSD, USDJPY, AUDCAD, "
        "GBPJPY, GBPUSD, EURUSD, EURJPY, US30, NAS100")
    st.info("Analysis: SMC + ICT + Multi Timeframe")
    st.info("Data: Twelve Data + yfinance backup")

if __name__ == "__main__":
    main()
