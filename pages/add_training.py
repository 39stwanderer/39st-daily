import streamlit as st
from datetime import datetime
from utils.data import load_data, save_data, get_current_day

def main():
    df = load_data()
    current_day = get_current_day(df)

    st.title(f"Add Daily Training – Day {current_day}")

    clamp_types = [
        "Metal spiked clover clamps",
        "Rubber spiked clover clamps",
        "Regular clover clamps",
        "Sleeveless nipple clamps",
        "Plastic clothespins",
        "Metal clothespins",
        "Alligator clips",
        "4-pronged claw clamps"
    ]

    with st.form("add_task_form", clear_on_submit=True):
        clamp = st.selectbox("Clamp type", clamp_types)

        st.subheader("Intensity Settings")

        # Initialize defaults
        if 'mins_value' not in st.session_state:
            st.session_state.mins_value = 10
        if 'tugs_value' not in st.session_state:
            st.session_state.tugs_value = 450

        col1, col2 = st.columns(2)

        with col1:
            mins = st.slider(
                "Clamped time (minutes)",
                5, 15, st.session_state.mins_value,
                step=1, key="add_mins"
            )

        with col2:
            tugs = st.slider(
                "Number of tugs",
                300, 600, st.session_state.tugs_value,
                step=10, key="add_tugs"
            )

        # Two-way sync
        if mins != st.session_state.mins_value:
            ratio = (mins - 5) / 10
            st.session_state.tugs_value = int(600 - ratio * 300)
            st.session_state.mins_value = mins
            st.rerun()

        if tugs != st.session_state.tugs_value:
            ratio = (tugs - 300) / 300
            st.session_state.mins_value = int(15 - ratio * 10)
            st.session_state.tugs_value = tugs
            st.rerun()

        reddit_user = st.text_input("Reddit username (optional)")

        submitted = st.form_submit_button("Submit training", type="primary", use_container_width=True)

        if submitted:
            new_row = {
                "Day": current_day,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Clamp Type": clamp,
                "Minutes": st.session_state.mins_value,
                "Tugs": st.session_state.tugs_value,
                "Reddit Username": reddit_user.strip(),
                "Status": "Pending",
                "Notes": ""
            }

            updated_df = df.concat([df, df.DataFrame([new_row])], ignore_index=True)
            save_data(updated_df)

            st.success(f"Training added for Day {current_day}!")
            st.balloons()

            # Reset
            st.session_state.mins_value = 10
            st.session_state.tugs_value = 450

            # Go back to home
            st.switch_page("pages/home.py")

    if st.button("← Back to Dashboard", type="secondary"):
        st.switch_page("pages/home.py")


if __name__ == "__main__":
    main()