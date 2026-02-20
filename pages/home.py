import streamlit as st
import pandas as pd
from utils.data import load_data, get_current_day, get_today_count
from components.auth import show_slave_login, show_logout_button

MAX_PER_DAY = 10

def main():
    st.title("Slave Daily Training Dashboard")

    df = load_data()
    current_day = get_current_day(df)
    today_count = get_today_count(df, current_day)

    # ─── Refresh ───
    if st.button("🔄 Refresh Data"):
        st.rerun()

    # ─── Stats ───
    completed = df[df["Status"] == "Completed"]
    total_completed = len(completed)
    clamp_counts = completed["Clamp Type"].value_counts()
    avg_mins = completed["Minutes"].mean() if not completed.empty else 0
    avg_tugs = completed["Tugs"].mean() if not completed.empty else 0

    st.subheader("Fun Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Completed Tasks", total_completed)
    col2.metric("Avg Clamped Time", f"{avg_mins:.1f} min" if avg_mins > 0 else "—")
    col3.metric("Avg Tugs", f"{avg_tugs:.0f}" if avg_tugs > 0 else "—")

    st.subheader("Clamp Type Breakdown")
    if not clamp_counts.empty:
        st.bar_chart(clamp_counts)
    else:
        st.info("No completed tasks yet.")

    # ─── Table ───
    st.subheader("All Tasks")
    if not df.empty:
        def highlight_completed(row):
            return ['background-color: #d4edda' if row["Status"] == "Completed" else '' for _ in row]

        st.dataframe(
            df.style.apply(highlight_completed, axis=1),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No tasks recorded yet.")

    # ─── Add button area ───
    st.divider()

    if today_count >= MAX_PER_DAY:
        st.warning(
            f"Daily limit reached ({today_count}/{MAX_PER_DAY}).\n"
            "Come back tomorrow!"
        )
    else:
        remaining = MAX_PER_DAY - today_count
        st.info(f"You can still add **{remaining}** more task{'s' if remaining != 1 else ''} today.")

        if st.button("➕ Add Daily Training", type="primary", use_container_width=True):
            st.switch_page("pages/add_training.py")

    # ─── Auth ───
    st.divider()
    if st.session_state.logged_in:
        show_logout_button()
    else:
        show_slave_login()


if __name__ == "__main__":
    main()