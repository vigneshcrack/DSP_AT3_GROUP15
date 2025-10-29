from typing import 
import streamlit as st
import pandas as pd

from tab_date.logics import DateColumn

# Explicit export to avoid name/visibility issues
__all__ = ["display_tab_date_content"]


def display_tab_date_content(
    file_path: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Create/refresh a DateColumn object, find datetime columns, let the user
    pick one, then show summary, chart and frequent values.
    """

    # ---- Load DataFrame if only a file path is given ----
    if df is None:
        if file_path:
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                st.error(f"Failed to read CSV from '{file_path}'. Error: {e}")
                return
        else:
            st.info("Please upload or provide a dataframe to explore datetime columns.")
            return

    # ---- Create/reuse DateColumn in session state (use keyword args!) ----
    if "tab_date_obj" not in st.session_state:
        st.session_state["tab_date_obj"] = DateColumn(file_path=file_path, df=df)
    else:
        obj: DateColumn = st.session_state["tab_date_obj"]
        obj.df = df
        obj.file_path = file_path

    date_obj: DateColumn = st.session_state["tab_date_obj"]

    # ---- Find datetime-like columns (support both method names) ----
    date_cols = None
    if hasattr(date_obj, "find_date_cols"):
        out = date_obj.find_date_cols()
        date_cols = out if isinstance(out, list) else getattr(date_obj, "cols_list", [])
    elif hasattr(date_obj, "datetime_columns"):
        date_cols = date_obj.datetime_columns()
    else:
        date_cols = []

    if not date_cols:
        st.warning("No datetime-like columns found in this dataset.")
        return

    # ---- Select column to explore ----
    selected_col = st.selectbox(
        "Which datetime column do you want to explore",
        options=date_cols,
        index=0,
        key="tab_date_select_col",
    )
    if not selected_col:
        return

    # ---- Compute/Render ----
    try:
        date_obj.set_data(selected_col)
    except Exception as e:
        st.error(f"Could not compute datetime metrics for '{selected_col}'. Error: {e}")
        return

    with st.expander("Date Column", expanded=True):
        # Summary
        try:
            st.table(date_obj.get_summary())
        except Exception as e:
            st.error(f"Error while generating summary: {e}")

        # Chart: prefer .histogram() if present; else .barchart attr
        try:
            chart = date_obj.histogram() if hasattr(date_obj, "histogram") and callable(date_obj.histogram) else getattr(date_obj, "barchart", None)
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error while generating histogram: {e}")

        # Frequent values (method or DataFrame attr)
        st.subheader("Most Frequent Values")
        try:
            freq_df = date_obj.frequent() if hasattr(date_obj, "frequent") and callable(date_obj.frequent) else getattr(date_obj, "frequent", None)
            if freq_df is not None:
                st.write(freq_df)
        except Exception as e:
            st.error(f"Error while listing frequent values: {e}")
