# tab_date/display.py
import streamlit as st
import pandas as pd
from tab_date.logics import DateColumn


def display_tab_date_content(file_path=None, df=None):
    """
    UI for the Datetime Serie tab.

    Behaviour:
      - Lists native datetime columns; if none, only highly date-parsable text columns.
      - If still none, shows an info message.
      - After selection, always attempts to parse and then displays either:
          * summary + chart + frequent table, or
          * a helpful message when the column can't be parsed.
    """
    # Keep a single DateColumn instance in session state
    if "date_tab" not in st.session_state:
        st.session_state.date_tab = DateColumn(file_path=file_path, df=df)
    else:
        if df is not None:
            st.session_state.date_tab.df = df
        if file_path is not None:
            st.session_state.date_tab.file_path = file_path

    datec: DateColumn = st.session_state.date_tab

    # Discover available datetime/date-like columns
    datec.find_date_cols()

    st.subheader("Datetime Serie")

    # Nothing to show? Exit gracefully.
    if not datec.cols_list:
        st.info("No datetime or date-like columns found in this dataset.")
        return

    # Select a column to explore
    selected_col = st.selectbox(
        "Which datetime column do you want to explore",
        datec.cols_list,
    )
    if not selected_col:
        return

    # Compute stats & visuals (handles both true datetime and text columns)
    datec.set_data(selected_col)

    # If parsing failed (all NaT), show a helpful message and a quick peek
    if datec.serie is None or datec.serie.dropna().empty:
        st.warning(
            f"Could not parse any dates from `{selected_col}`. "
            "Here are a few raw values from the original column to investigate formats."
        )
        try:
            raw = st.session_state.date_tab.df[selected_col].dropna().astype(str).head(20)
            st.dataframe(pd.DataFrame({"sample_values": raw}), use_container_width=True)
        except Exception:
            pass
        return

    # Summary table
    with st.expander("Date Column", expanded=True):
        st.table(datec.get_summary())

    # Histogram / bar chart
    st.altair_chart(datec.barchart, use_container_width=True)

    # Top-20 frequency table
    st.subheader("Most Frequent Values")
    st.dataframe(datec.frequent, use_container_width=True)
