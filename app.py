import streamlit as st
import pandas as pd
import altair as alt
import json
import os
import hashlib
from datetime import datetime, timedelta, date

# ---------- CONFIG ----------
st.set_page_config(page_title="WaterBuddy — SipSmart", page_icon="💧", layout="centered")

# ---------- THEME ----------
page_bg = """
<style>
.stApp {
    background: linear-gradient(135deg, #aee1f9 0%, #89cff0 40%, #4682b4 100%);
    color: #ffffff;
    font-family: 'Poppins', sans-serif;
}
h1, h2, h3 {
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
.stProgress > div > div > div > div {
    background-color: #00BFFF;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- FILE ----------
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

# ---------- PASSWORD UTILS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, entered_password):
    return stored_hash == hashlib.sha256(entered_password.encode()).hexdigest()

# ---------- SESSION ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- NAV ----------
def navbar():
    pages = ["Dashboard", "Log Water"]
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if st.session_state.page == p:
            cols[i].markdown(f"**➡️ {p}**")
        elif cols[i].button(p):
            st.session_state.page = p
    st.markdown("---")

# ---------- USER ----------
def ensure_user(name):
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {"name": name},
            "password": "",
            "history": {}
        }
    return data["users"][name]

# ---------- LOGIN / SIGNUP ----------
if st.session_state.page == "Login":
    st.title("💧 WaterBuddy — SipSmart")
    st.subheader("Hydrate Smart. Feel Great.")

    tab1, tab2 = st.tabs(["🔐 Login", "🆕 Sign Up"])

    # --- LOGIN TAB ---
    with tab1:
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        if st.button("Login"):
            if username in data["users"]:
                user = data["users"][username]
                if verify_password(user["password"], password):
                    st.session_state.user = username
                    st.session_state.page = "Dashboard"
                    st.success(f"Welcome back, {username}! 💦")
                else:
                    st.error("❌ Incorrect password.")
            else:
                st.warning("⚠️ User not found. Please sign up first.")

    # --- SIGNUP TAB ---
    with tab2:
        new_user = st.text_input("Choose a username:")
        new_pass = st.text_input("Create password:", type="password")
        if st.button("Sign Up"):
            if not new_user.strip() or not new_pass.strip():
                st.warning("Please fill all fields!")
            elif new_user in data["users"]:
                st.error("Username already exists! Choose another.")
            elif any(u["password"] == hash_password(new_pass) for u in data["users"].values()):
                st.error("This password is already used by another user. Choose a new one.")
            else:
                data["users"][new_user] = {
                    "profile": {"name": new_user},
                    "password": hash_password(new_pass),
                    "history": {}
                }
                save_data(data)
                st.success("✅ Account created successfully! You can now log in.")

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header(f"📊 Dashboard — {user['profile']['name']}")

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

    if st.button("Add Drink"):
        amt = amount or custom
        ds = today_str()
        if ds not in user["history"]:
            user["history"][ds] = {"total_ml": 0, "entries": []}
        tnow = datetime.now().strftime("%H:%M:%S")
        user["history"][ds]["entries"].append({"time": tnow, "ml": int(amt)})
        user["history"][ds]["total_ml"] += int(amt)
        save_data(data)
        st.success(f"Logged {amt} ml at {tnow}")

    # ---------- Mascot (GIF based on progress) ----------
    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal_ml = 2000
    progress = today_total / daily_goal_ml

    if progress < 0.2:
        mascot_gif = ""C:\Users\Harini Priya\Downloads\stay-hydrated 1.gif""

    elif progress < 1.0:
        mascot_gif = ""C:\Users\Harini Priya\Downloads\happy-cute hydration 2.gif""

    st.image(mascot_gif, width=250)

    # ---------- Today's Log ----------
    st.markdown("### 💧 Today's Log")
    ds = today_str()
    if ds in user["history"] and user["history"][ds]["entries"]:
        df = pd.DataFrame(user["history"][ds]["entries"])
        st.table(df)
    else:
        st.info("No entries yet — log your first drink!")

save_data(data)
