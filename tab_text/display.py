# tab_text/display.py
import os
import streamlit as st
import pandas as pd
from typing import Optional

from tab_text.logics import TextColumn


def display_tab_text_content(file_path: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> None:
    """
    Instantiates TextColumn, stores it in session, finds text columns, lets the
    user pick one, then shows summary, chart, and frequent values.
    """

    # --- Load dataframe if only file_path is provided ---
    if df is None:
        if file_path:
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                st.error(f"Failed to read CSV from '{file_path}'. Error: {e}")
                return
        else:
            st.info("Please upload or provide a dataframe to explore text columns.")
            return

    # --- If a stale object has a DataFrame in file_path, drop it ---
    if "tab_text_obj" in st.session_state:
        obj = st.session_state["tab_text_obj"]
        if hasattr(obj, "file_path") and not (
            obj.file_path is None or isinstance(obj.file_path, (str, os.PathLike))
        ):
            st.session_state.pop("tab_text_obj")

    # --- Create/reuse TextColumn (PASS KEYWORD ARGS!) ---
    if "tab_text_obj" not in st.session_state:
        st.session_state["tab_text_obj"] = TextColumn(file_path=file_path, df=df)
    else:
        obj: TextColumn = st.session_state["tab_text_obj"]
        obj.df = df
        obj.file_path = file_path

    text_obj: TextColumn = st.session_state["tab_text_obj"]

    # --- Find text columns ---
    text_cols = text_obj.find_text_cols()
    if not text_cols:
        st.warning("No text-like columns detected in the dataset.")
        return

    # --- Select column ---
    selected_col = st.selectbox(
        "Which text column do you want to explore",
        options=text_cols,
        index=0,
        key="tab_text_select_col",
    )
    if not selected_col:
        return

    # --- Compute & render ---
    try:
        text_obj.set_data(selected_col)
    except Exception as e:
        st.error(f"Could not compute text metrics for '{selected_col}'. Error: {e}")
        return

    with st.expander("Text Column Analysis", expanded=True):
        try:
            st.table(text_obj.get_summary())
        except Exception as e:
            st.error(f"Error generating summary: {e}")

        try:
            chart = text_obj.histogram()
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering bar chart: {e}")

        st.subheader("Most Frequent Values")
        try:
            st.write(text_obj.frequent())
        except Exception as e:
            st.error(f"Error displaying frequent values: {e}")

#hiiii
    