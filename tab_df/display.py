# tab_df/display.py
import streamlit as st
import pandas as pd
from tab_df.logics import Dataset


def display_tab_df_content(file_path: str) -> None:
    """
    Creates/updates a Dataset in session state, computes summary & columns table,
    and provides head/tail/sample exploration with a slider and radio buttons.
    Also stores the Dataset object into st.session_state['dataset'] so other tabs
    (numeric/text/date) can reuse df via st.session_state.dataset.df.
    """
    if not file_path:
        st.warning("No file path provided.")
        return

    # ---- Create/refresh Dataset in session state ----
    if "tab_df_obj" not in st.session_state:
        st.session_state["tab_df_obj"] = Dataset(file_path)
    else:
        st.session_state["tab_df_obj"].file_path = file_path

    df_obj: Dataset = st.session_state["tab_df_obj"]

    try:
        df_obj.set_data()
    except Exception as e:
        st.error(f"Could not load or process dataset. Error: {e}")
        return

    # Make the dataset available to other tabs
    st.session_state["dataset"] = df_obj
    st.session_state["df"] = df_obj.df

    # ---- Overview Expander ----
    with st.expander("Overall DataFrame Information", expanded=True):
        st.subheader("Dataset Summary")
        st.table(df_obj.get_summary())

        st.subheader("Columns Information")
        st.write(df_obj.table)

    # ---- Row Exploration Expander ----
    with st.expander("Explore Dataset Rows", expanded=True):
        st.markdown("### Data Preview")
        n = st.slider("Select number of rows to display", 5, 50, 10, 1)
        method = st.radio(
            "Select display method",
            options=["Head", "Tail", "Sample"],
            horizontal=True,
            index=0,
        )

        # Call the appropriate method (no 'method' kwarg for get_sample)
        method_l = method.lower()
        try:
            if method_l == "head":
                subset = df_obj.get_head(n=n)
            elif method_l == "tail":
                subset = df_obj.get_tail(n=n)
            else:
                subset = df_obj.get_sample(n=n)

            st.dataframe(subset, use_container_width=True)
        except Exception as e:
            st.error(f"Error while generating subset of data: {e}")


