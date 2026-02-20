import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data() -> pd.DataFrame:
    conn = get_connection()
    df = conn.read(worksheet=0, usecols=[0,1,2,3,4,5,6,7], header=0)
    
    if df.empty:
        df = pd.DataFrame(columns=[
            "Day", "Timestamp", "Clamp Type", "Minutes", "Tugs",
            "Reddit Username", "Status", "Notes"
        ])
    
    df["Day"] = pd.to_numeric(df["Day"], errors='coerce').fillna(0).astype(int)
    return df.sort_values("Day", ascending=False)


def save_data(df: pd.DataFrame):
    conn = get_connection()
    conn.update(worksheet=0, data=df)


def get_current_day(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    return int(df["Day"].max() + 1)


def get_today_count(df: pd.DataFrame, current_day: int) -> int:
    return len(df[df["Day"] == current_day])