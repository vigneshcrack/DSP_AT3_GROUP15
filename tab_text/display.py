# tab_text/display.py
import streamlit as st
from tab_text.logics import TextColumn


def display_tab_text_content(file_path=None, df=None):
    """
    UI for the Text Serie tab
    """
    if "text_tab" not in st.session_state:
        st.session_state.text_tab = TextColumn(file_path=file_path, df=df)
    else:
        if df is not None:
            st.session_state.text_tab.df = df
        if file_path is not None:
            st.session_state.text_tab.file_path = file_path

    txt = st.session_state.text_tab
    txt.find_text_cols()

    st.subheader("Text Serie")
    if not txt.cols_list:
        st.info("No text-like columns found.")
        return

    sel = st.selectbox("Which text column do you want to explore", txt.cols_list)
    if sel:
        txt.set_data(sel)

        with st.expander("Text Column", expanded=True):
            st.table(txt.get_summary())

        st.altair_chart(txt.barchart, use_container_width=True)

        st.subheader("Most Frequent Values")
        st.dataframe(txt.frequent, use_container_width=True)
