# tab_num/display.py
import streamlit as st
import altair as alt
import pandas as pd
from .logics import get_numeric_columns, compute_numeric_summary, get_value_frequencies


def display_numeric_tab(df: pd.DataFrame):
    """Render numeric tab with summary stats, top values, and visual distribution."""
    
    st.header("📊 Numeric Column Analysis")

    if df is None or df.empty:
        st.warning("Upload a CSV file to start numeric analysis.")
        return

    # --- Detect numeric columns ---
    numeric_cols = get_numeric_columns(df)
    if not numeric_cols:
        st.info("No numeric columns detected in this dataset.")
        return

    # --- Column selection ---
    selected_col = st.selectbox("Select a numeric column:", numeric_cols)
    if not selected_col:
        return

    # --- Session persistence (avoid recalculating on rerun) ---
    key_obj = f"num_obj_{selected_col}"
    if key_obj not in st.session_state:
        st.session_state[key_obj] = {
            "summary": compute_numeric_summary(df, selected_col),
            "freq_df": get_value_frequencies(df, selected_col)
        }

    summary = st.session_state[key_obj]["summary"]
    freq_df = st.session_state[key_obj]["freq_df"]

    # --- Summary Table ---
    st.subheader("Summary Statistics")
    summary_df = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])
    summary_df["Value"] = summary_df["Value"].apply(
        lambda x: f"{x:.2f}" if isinstance(x, float) else int(x)
    )
    st.table(summary_df)

    # --- Top 20 most frequent values ---
    st.subheader("Top 20 Most Frequent Values")
    freq_df["Percentage (%)"] = freq_df["Percentage (%)"].round(2)
    st.dataframe(freq_df, use_container_width=True)

    # --- Distribution chart ---
    st.subheader("Value Frequency Distribution")
    unique_vals = df[selected_col].nunique()

    if unique_vals <= 30:
        # Low-cardinality → bar chart
        chart = (
            alt.Chart(freq_df)
            .mark_bar(color="#1f77b4")
            .encode(
                x=alt.X("Value:O", sort="-y", title="Value"),
                y=alt.Y("Count:Q", title="Frequency"),
                tooltip=["Value", "Count", "Percentage (%)"]
            )
            .properties(title=f"Value Distribution – {selected_col}", height=400)
            .interactive()
        )
    else:
        # High-cardinality → histogram
        hist_series = pd.to_numeric(df[selected_col], errors="coerce").dropna()
        hist_df = pd.DataFrame({selected_col: hist_series})
        chart = (
            alt.Chart(hist_df)
            .mark_bar(color="#ff7f0e")
            .encode(
                x=alt.X(f"{selected_col}:Q", bin=alt.Bin(maxbins=30), title="Value Range"),
                y=alt.Y("count()", title="Frequency")
            )
            .properties(title=f"Histogram – {selected_col}", height=400)
            .interactive()
        )
        st.caption("High unique values detected → histogram with 30 bins.")

    st.altair_chart(chart, use_container_width=True)
