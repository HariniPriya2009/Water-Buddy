import streamlit as st
import sqlite3
from datetime import datetime, date
import json

# ---------------------------------------------------------
#                 DATABASE SETUP
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("waterbuddy.db")
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age_group TEXT,
            name TEXT
        )
    """)

    # WATER LOGS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
#                DATABASE ACTION FUNCTIONS
# ---------------------------------------------------------
def create_user(username, password, name, age_group):
    conn = sqlite3.connect("waterbuddy.db")
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password, age_group, name) VALUES (?, ?, ?, ?)",
            (username, password, age_group, name)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def validate_user(username, password):
    conn = sqlite3.connect("waterbuddy.db")
    cur = conn.cursor()

    cur.execute("SELECT id, name, age_group FROM users WHERE username=? AND password=?",
                (username, password))
    row = cur.fetchone()

    conn.close()
    return row  # returns (id, name, age_group)


def add_water_log(user_id, amount):
    conn = sqlite3.connect("waterbuddy.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO logs (user_id, amount, timestamp) VALUES (?, ?, ?)",
        (user_id, amount, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_today_logs(user_id):
    conn = sqlite3.connect("waterbuddy.db")
    cur = conn.cursor()

    today = date.today().isoformat()

    cur.execute("""
        SELECT amount, timestamp FROM logs
        WHERE user_id = ? AND timestamp LIKE ?
    """, (user_id, today + "%"))

    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
#                 STREAMLIT UI
# ---------------------------------------------------------

st.set_page_config(page_title="WaterBuddy", page_icon="💧")

init_db()

if "page" not in st.session_state:
    st.session_state.page = "Login"

if "user" not in st.session_state:
    st.session_state.user = None


# ---------------------------------------------------------
#                     NAVBAR
# ---------------------------------------------------------
def navbar():
    pages = ["Dashboard", "Log Water", "Settings"]

    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if st.session_state.page == p:
            cols[i].markdown(f"**➡️ {p}**")
        elif cols[i].button(p):
            st.session_state.page = p
            st.rerun()

    st.write("---")


# ---------------------------------------------------------
#                       LOGIN PAGE
# ---------------------------------------------------------
if st.session_state.page == "Login":
    st.title("💧 WaterBuddy Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        result = validate_user(username, password)

        if result:
            user_id, name, age_group = result
            st.session_state.user = {"id": user_id, "name": name, "age_group": age_group}
            st.session_state.page = "Dashboard"
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials. Try again.")

    if st.button("Create Account"):
        st.session_state.page = "Signup"
        st.rerun()


# ---------------------------------------------------------
#                       SIGNUP PAGE
# ---------------------------------------------------------
elif st.session_state.page == "Signup":
    st.title("📝 Create Your WaterBuddy Account")

    name = st.text_input("Full Name")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    age_group = st.selectbox("Age Group", ["Child", "Teen", "Adult", "Senior"])

    if st.button("Create Account"):
        if create_user(username, password, name, age_group):
            st.success("Account created! Please login.")
            st.session_state.page = "Login"
            st.rerun()
        else:
            st.error("Username already exists. Choose another one.")

    if st.button("Back to Login"):
        st.session_state.page = "Login"
        st.rerun()


# ---------------------------------------------------------
#                     DASHBOARD PAGE
# ---------------------------------------------------------
elif st.session_state.page == "Dashboard":
    navbar()
    st.header(f"👋 Welcome, {st.session_state.user['name']}!")

    logs = get_today_logs(st.session_state.user["id"])
    total = sum([l[0] for l in logs])

    st.subheader(f"Today's Water Intake: **{total} ml**")

    if logs:
        st.write("Your logs:")
        for amount, time in logs:
            st.write(f"• {amount} ml at {time.split('T')[1][:5]}")
    else:
        st.info("No water logged yet today.")


# ---------------------------------------------------------
#                    LOG WATER PAGE
# ---------------------------------------------------------
elif st.session_state.page == "Log Water":
    navbar()
    st.header("💧 Log Water Intake")

    amount = st.number_input("Amount (ml)", min_value=50, max_value=2000, step=50)

    if st.button("Add Log"):
        add_water_log(st.session_state.user["id"], amount)
        st.success("Logged successfully!")
        st.rerun()


# ---------------------------------------------------------
#                     SETTINGS PAGE
# ---------------------------------------------------------
elif st.session_state.page == "Settings":
    navbar()

    st.header("⚙️ Settings")
    st.write(f"**Name:** {st.session_state.user['name']}")
    st.write(f"**Age Group:** {st.session_state.user['age_group']}")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "Login"
        st.rerun()
