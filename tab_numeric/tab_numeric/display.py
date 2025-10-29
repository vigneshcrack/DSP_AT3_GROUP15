# tab_num/display.py
import streamlit as st
import pandas as pd
from typing import Optional

from tab_num.logics import NumericColumn


def display_tab_num_content(file_path: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> None:
    """
    Instantiates tab_num.logics.NumericColumn, stores it in Streamlit session state,
    finds numeric columns, lets the user pick one, and shows summary, histogram,
    and most frequent values. Compatible with both attribute- and method-based APIs.
    """

    # --- Load dataframe if only a file path is provided ---
    if df is None:
        if file_path:
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                st.error(f"Failed to read CSV from '{file_path}'. Error: {e}")
                return
        else:
            st.info("Please upload or provide a dataframe to explore numeric columns.")
            return

    # --- Create or reuse NumericColumn object in session state (use kwargs!) ---
    if "tab_num_obj" not in st.session_state:
        st.session_state["tab_num_obj"] = NumericColumn(file_path=file_path, df=df)
    else:
        obj = st.session_state["tab_num_obj"]
        obj.df = df
        obj.file_path = file_path

    num_obj: NumericColumn = st.session_state["tab_num_obj"]

    # --- Find numeric columns ---
    num_cols = num_obj.find_num_cols()
    if not num_cols:
        st.warning("No numeric columns detected in the dataset.")
        return

    # --- Select column to explore ---
    selected_col = st.selectbox(
        "Which numeric column do you want to explore",
        options=num_cols,
        index=0,
        key="tab_num_select_col",
    )
    if not selected_col:
        return

    # --- Compute metrics for selected column ---
    try:
        num_obj.set_data(selected_col)
    except Exception as e:
        st.error(f"Could not compute numeric metrics for '{selected_col}'. Error: {e}")
        return

    # --- Display results inside an Expander ---
    with st.expander("Numeric Column Analysis", expanded=True):
        # Summary Table
        try:
            st.table(num_obj.get_summary())
        except Exception as e:
            st.error(f"Error generating summary: {e}")

        # Histogram (supports method or attribute)
        try:
            chart = None
            # prefer callable method if present
            if hasattr(num_obj, "histogram") and callable(getattr(num_obj, "histogram")):
                chart = num_obj.histogram()
            else:
                # else treat as attribute
                chart = getattr(num_obj, "histogram", None)

            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering histogram: {e}")

        # Most Frequent Values (supports method or attribute)
        st.subheader("Most Frequent Values")
        try:
            if hasattr(num_obj, "frequent") and callable(getattr(num_obj, "frequent")):
                freq_df = num_obj.frequent()
            else:
                freq_df = getattr(num_obj, "frequent", None)

            if freq_df is not None:
                st.write(freq_df)
        except Exception as e:
            st.error(f"Error displaying frequent values: {e}")

    
