# utils/data.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        # Load from secrets
        cred_dict = st.secrets["firebase"]
        cred = credentials.Certificate(dict(cred_dict))
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def load_data() -> pd.DataFrame:
    db = get_db()
    docs = (
        db.collection("trainings")
        .order_by("Day", direction=firestore.Query.DESCENDING)
        .stream()
    )
    
    data = [doc.to_dict() for doc in docs]
    if not data:
        return pd.DataFrame(columns=[
            "Day", "Timestamp", "Clamp Type", "Minutes", "Tugs",
            "Reddit Username", "Status", "Notes"
        ])
    
    df = pd.DataFrame(data)
    df["Day"] = pd.to_numeric(df["Day"], errors='coerce').fillna(0).astype(int)
    return df.sort_values("Day", ascending=False)


def save_training(new_row_dict: dict):
    db = get_db()
    # Option A: auto-generated ID
    db.collection("trainings").add(new_row_dict)
    
    # Option B: deterministic ID (e.g. day + timestamp) to avoid duplicates
    # doc_id = f"day_{new_row_dict['Day']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # db.collection("trainings").document(doc_id).set(new_row_dict)


def get_current_day(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    return int(df["Day"].max() + 1)


def get_today_count(df: pd.DataFrame, current_day: int) -> int:
    return len(df[df["Day"] == current_day])