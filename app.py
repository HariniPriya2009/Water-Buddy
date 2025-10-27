import streamlit as st
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime, timedelta, date, time  # Added time import
import requests

# ---------- CONFIG ----------
st.set_page_config(page_title="WaterBuddy — SipSmart", page_icon="💧", layout="centered")

# ---------- STYLE ----------
page_bg = """
<style>
.stApp {
    background: linear-gradient(135deg, #89CFF0 0%, #4682B4 50%, #1E90FF 100%);
    color: white;
    font-family: 'Poppins', sans-serif;
}
h1, h2, h3, h4 {
    color: #ffffff !important;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
}
div.stButton > button:first-child {
    background: linear-gradient(90deg, #1E90FF, #00BFFF);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 0.6em 1.5em;
    font-weight: 600;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}
div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #00BFFF, #1E90FF);
    transform: scale(1.05);
}
input, textarea, select {
    border-radius: 10px !important;
    border: 1px solid #87CEFA !important;
}
.stProgress > div > div > div > div {
    background-color: #00BFFF;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- FILE HANDLING ----------
DATA_FILE = "waterbuddy_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def today_str():
    return date.today().isoformat()

# ---------- LOAD LOTTIE ----------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            st.warning(f"Failed to load animation: Status {r.status_code}")
            return None
        return r.json()
    except Exception as e:
        st.warning(f"Error loading animation: {str(e)}")
        return None

# ---------- INIT ----------
data = load_data()
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- NAVBAR ----------
def navbar():
    pages = ["Dashboard", "Log Water", "Challenges", "Badges", "Settings"]
    if st.session_state.user:
        cols = st.columns(len(pages))
        for i, p in enumerate(pages):
            if st.session_state.page == p:
                cols[i].markdown(f"**➡️ {p}**")
            elif cols[i].button(p):
                st.session_state.page = p
                st.rerun()
    st.markdown("---")

# ---------- USER MANAGEMENT ----------
def ensure_user(name):
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {"name": name, "age_group": None},
            "settings": {
                "reminder_enabled": False,
                "reminder_minutes": 120,
                "reminder_start_time": "09:00"
            },
            "history": {},
            "badges": [],
            "challenges": []
        }
    return data["users"][name]

# ---------- LOGIN ----------
if st.session_state.page == "Login":
    st.title("💧 WaterBuddy — SipSmart")
    st.subheader("Hydrate Your Lifestyle with Smart Tracking")
    st.markdown("---")

    # Use a working Lottie animation URL
    bg_anim = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_qjogjzsr.json")
    if bg_anim:
        st_lottie(bg_anim, speed=1, height=200, key="bg", loop=True)
    else:
        st.info("💧 Welcome to WaterBuddy!")

    name = st.text_input("Enter your name:")
    age = st.radio("Select your age group:", ["<18", "18–30", "31–50", "50+"], horizontal=True)

    if st.button("Start 🚀"):
        if not name.strip():
            st.warning("Please enter your name!")
        else:
            st.session_state.user = name.strip()
            user = ensure_user(st.session_state.user)
            user["profile"]["age_group"] = age
            save_data(data)
            st.session_state.page = "Dashboard"
            st.success(f"Welcome {name}! You're all set 🎉")
            st.rerun()

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header(f"📊 Dashboard — {user['profile']['name']}")

    # Past 7 days graph
    dates, totals = [], []
    for d in range(6, -1, -1):
        dd = date.today() - timedelta(days=d)
        dates.append(dd)
        totals.append(user["history"].get(dd.isoformat(), {}).get("total_ml", 0) / 1000)

    df = pd.DataFrame({"Date": dates, "Litres": totals})

    chart = alt.Chart(df).mark_bar(color="#00BFFF").encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Litres:Q", title="Water Intake (L)"),
        tooltip=["Date:T", "Litres:Q"]
    ).properties(title="Past 7 Days Water Intake")
    st.altair_chart(chart, use_container_width=True)

    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    st.metric("Today's Intake", f"{today_total/1000:.2f} L")
    progress = min(1, today_total / 2000)
    st.progress(progress)

    # Reset daily progress
    st.markdown("### 🔁 Daily Reset")
    if st.button("Reset Today's Progress"):
        ds = today_str()
        if ds in user["history"]:
            user["history"][ds] = {"total_ml": 0, "entries": []}
            save_data(data)
            st.success("Today's progress reset.")
            st.rerun()
        else:
            st.info("No entries to reset yet.")

# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header("💦 Log Water Intake")

    col1, col2, col3, col4 = st.columns(4)
    amount = None
    if col1.button("200 ml"): amount = 200
    if col2.button("250 ml"): amount = 250
    if col3.button("300 ml"): amount = 300
    if col4.button("500 ml"): amount = 500

    custom = st.number_input("Custom amount (ml):", 100, 1000, 250, 50)

    if st.button("Add Drink 💧"):
        amt = amount or custom
        ds = today_str()
        if ds not in user["history"]:
            user["history"][ds] = {"total_ml": 0, "entries": []}
        tnow = datetime.now().strftime("%H:%M:%S")
        user["history"][ds]["entries"].append({"time": tnow, "ml": int(amt)})
        user["history"][ds]["total_ml"] += int(amt)
        save_data(data)
        st.success(f"Added {amt} ml!")
        st.rerun()

    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal_ml = 2000
    progress = today_total / daily_goal_ml

    # Working Lottie URLs - Use LottieFiles public animations
    if progress < 0.2:
        mascot_url = "https://assets9.lottiefiles.com/packages/lf20_qh5z2fdq.json"  # Sad/thirsty
        message = "🌵 You're dehydrated! Start sipping!"
    elif progress < 0.5:
        mascot_url = "https://assets2.lottiefiles.com/packages/lf20_touohxv0.json"  # Happy
        message = "😊 Good start! Keep it up!"
    elif progress < 1.0:
        mascot_url = "https://assets1.lottiefiles.com/packages/lf20_x62chJ.json"  # Strong
        message = "💪 Almost there! You're doing great!"
    else:
        mascot_url = "https://assets4.lottiefiles.com/packages/lf20_aEFaHc.json"  # Celebrate
        message = "🎉 Goal achieved! Excellent job!"

    st.markdown(f"### {message}")
    
    # Load and display mascot
    mascot_animation = load_lottieurl(mascot_url)
    if mascot_animation:
        # Use a unique key based on progress to force re-rendering
        st_lottie(mascot_animation, height=300, key=f"mascot_{int(progress*100)}")
    else:
        # Fallback emoji display if Lottie fails
        emoji_map = {0: "😢", 0.2: "🙂", 0.5: "😊", 1.0: "🎉"}
        for threshold, emoji in sorted(emoji_map.items(), reverse=True):
            if progress >= threshold:
                st.markdown(f"<h1 style='text-align:center;font-size:150px;'>{emoji}</h1>", unsafe_allow_html=True)
                break

    st.progress(min(progress, 1.0))
    st.write(f"**Today's Intake:** {today_total} ml / {daily_goal_ml} ml")

    st.markdown("<h3 style='color:white;'>🧾 Today's Log</h3>", unsafe_allow_html=True)
    ds = today_str()
    if ds in user["history"] and user["history"][ds]["entries"]:
        df = pd.DataFrame(user["history"][ds]["entries"])
        st.table(df)
    else:
        st.info("No entries yet — log your first drink!")

# ---------- CHALLENGES ----------
elif st.session_state.page == "Challenges":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header("🏁 Challenges")

    # Cleanup old challenges without 'goal'
    for ch in user["challenges"]:
        if "goal" not in ch:
            ch["goal"] = 2.0
    save_data(data)

    ch_name = st.text_input("Challenge name:")
    days = st.slider("Duration (days)", 1, 30, 7)
    daily_goal = st.slider("Daily goal (litres)", 0.5, 5.0, 2.0, 0.25)
    if st.button("Create Challenge"):
        user["challenges"].append({
            "name": ch_name or f"{daily_goal}L × {days}d",
            "days": days,
            "goal": daily_goal,
            "start": today_str(),
            "done": False
        })
        save_data(data)
        st.success("Challenge created!")
        st.rerun()

    if user["challenges"]:
        st.subheader("Your Challenges")
        for ch in user["challenges"]:
            st.write(
                f"**{ch.get('name', 'Unnamed Challenge')}** — "
                f"{ch.get('days', '?')} days, "
                f"{ch.get('goal', '?')} L/day — "
                f"Started {ch.get('start', '?')}"
            )

# ---------- BADGES ----------
elif st.session_state.page == "Badges":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header("🏅 Your Badges")
    if not user["badges"]:
        st.info("No badges yet — keep hydrating to earn them!")
    else:
        for b in user["badges"]:
            st.success(f"🏆 {b}")

# ---------- SETTINGS ----------
elif st.session_state.page == "Settings":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header("⚙️ Settings")

    st.subheader("🔔 Reminder Settings")
    rem_enabled = st.checkbox(
        "Enable in-app reminders (works while app is open)",
        value=user["settings"].get("reminder_enabled", False)
    )
    rem_minutes = st.number_input(
        "Reminder interval (minutes):", min_value=15, max_value=720,
        value=user["settings"].get("reminder_minutes", 120), step=15
    )
    rem_start = st.time_input(
        "Start reminders at:",
        value=time.fromisoformat(user["settings"].get("reminder_start_time", "09:00"))
    )

    if st.button("💾 Save Reminder Settings"):
        user["settings"]["reminder_enabled"] = rem_enabled
        user["settings"]["reminder_minutes"] = int(rem_minutes)
        user["settings"]["reminder_start_time"] = rem_start.strftime("%H:%M")
        save_data(data)
        st.success("Reminder settings saved!")

    st.markdown("---")
    st.subheader("🗑️ Reset All Data")
    st.warning("This will delete all your logs, badges, and progress.")
    confirm = st.checkbox("I confirm I want to delete all my data.")
    if confirm and st.button("Reset All Data"):
        data["users"].pop(st.session_state.user, None)
        save_data(data)
        st.session_state.user = None
        st.session_state.page = "Login"
        st.success("All data deleted. You are now logged out.")
        st.rerun()

# ---------- SAVE ----------
save_data(data)

