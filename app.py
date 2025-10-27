import streamlit as st
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime, timedelta, date, time
import requests
import hashlib
from streamlit_lottie import st_lottie   # ✅ required for Lottie animations

# ---------- CONFIG ----------
st.set_page_config(page_title="Hydration Login", layout="centered")

# ---------- FUNCTIONS ----------
def hash_password(password):
    """Hashes the password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Loads saved user data from JSON file."""
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    """Saves user data to JSON file."""
    with open("users.json", "w") as file:
        json.dump(users, file)
