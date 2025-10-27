import streamlit as st
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime, timedelta, date, time

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

data = load_data()

# ---------- INIT ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- NAVBAR ----------
def navbar():
    pages = ["Dashboard", "Log Water", "Challenges", "Badges", "Settings"]
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if st.session_state.page == p:
            cols[i].markdown(f"**➡️ {p}**")
        elif cols[i].button(p):
            st.session_state.page = p
            st.rerun()
    st.markdown("---")

# ---------- USER MANAGEMENT ----------
def ensure_user(name, password):
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {"name": name, "password": password, "age_group": None},
            "history": {},
            "badges": [],
            "challenges": [],
            "settings": {
                "reminder_enabled": False,
                "reminder_minutes": 120,
                "reminder_start_time": "09:00"
            }
        }
    return data["users"][name]

# ---------- LOGIN ----------
if st.session_state.page == "Login":
    st.markdown("<h1 style='color:white;text-align:center;font-size:48px;'>Welcome to WaterBuddy!</h1>", unsafe_allow_html=True)
    st.subheader("💧 Hydrate Your Lifestyle with Smart Tracking")
    st.markdown("---")

    name = st.text_input("Enter your name:")
    password = st.text_input("Set a password:", type="password")
    age = st.radio("Select your age group:", ["<18", "18–30", "31–50", "50+"], horizontal=True)

    if st.button("Start 🚀"):
        if not name.strip() or not password.strip():
            st.warning("Please enter both name and password!")
        elif any(u["profile"]["password"] == password for u in data["users"].values()):
            st.error("Password already in use! Choose a different one.")
        else:
            st.session_state.user = name.strip()
            user = ensure_user(st.session_state.user, password)
            user["profile"]["age_group"] = age
            save_data(data)
            st.session_state.page = "Dashboard"
            st.success(f"Welcome {name}! You're all set 🎉")
            st.rerun()

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    user = data["users"][st.session_state.user]
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
    st.progress(min(1, today_total / 2000))

# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    user = data["users"][st.session_state.user]
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
        st.session_state.gif_state = "updated"
        st.success(f"Added {amt} ml! 💧")
        st.rerun()

    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    progress = today_total / 2000

    # Change mascot based on progress
    if progress < 0.2:
        mascot_path = r"image/happy-cute hydration 2.gif"
        message = "🌵 You're dehydrated! Start sipping!"
    elif progress < 0.5:
        mascot_path = r"C:\Users\Harini Priya\AppData\Local\Programs\Python\Python310\water buddy\happy-cute hydration 2.gif"
        message = "😊 Good start! Keep it up!"
    elif progress < 1.0:
        mascot_path = "mascots/strong.gif"
        message = "💪 Almost there! You're doing great!"
    else:
        mascot_path = "mascots/celebrate.gif"
        message = "🎉 Goal achieved! Excellent job!"

    st.markdown(f"### {message}")
    st.image(mascot_path, use_container_width=False)

    st.progress(min(progress, 1.0))
    st.write(f"**Today's Intake:** {today_total} ml / 2000 ml")

# ---------- SAVE ----------
save_data(data)



