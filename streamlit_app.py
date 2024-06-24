import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from stocks import *
from commodities import *

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")

option = st.selectbox(
   "Select",
   ("Equity", "Commodities")
)
if option == 'Equity':
    uploaded_files = st.file_uploader("Choose a PDF file", accept_multiple_files=False)
    if uploaded_files is not None:
        df_new = pdf_to_excel_equity(uploaded_files)
        df_new = df_new.fillna("")
        st.dataframe(df_new)
        csv_data = convert_df(df_new)
        btn = st.download_button(
        label="Download",
        data=csv_data,
        file_name="Stock Summary.csv",
        mime="text/csv",)
if option == 'Commodities':
     uploaded_files1 = st.file_uploader("Choose a PDF file", accept_multiple_files=False)
     if uploaded_files1 is not None:
        df_new = pdf_to_excel_commodities(uploaded_files1)
        df_new = df_new.fillna("")
        st.dataframe(df_new)
        csv_data = convert_df(df_new)
        btn = st.download_button(
        label="Download",
        data=csv_data,
        file_name="Commodity Summary.csv",
        mime="text/csv",)