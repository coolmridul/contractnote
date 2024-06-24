import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from stocks import *


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")

uploaded_files = st.file_uploader("Choose a PDF file", accept_multiple_files=False)
if uploaded_files is not None:
    df_new = pdf_to_excel_equity(uploaded_files)
    df_new = df_new.fillna("NA")
    st.dataframe(df_new)
    csv_data = convert_df(df_new)
    btn = st.download_button(
    label="Download",
    data=csv_data,
    file_name="Stock Summary.csv",
    mime="text/csv",)