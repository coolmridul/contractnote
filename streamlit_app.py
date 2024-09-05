import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from hdfc_sec_stocks import *
from commodities import *
from emkay_future import *
from emkay_equity import *
from nakamichi_fut import *

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")

option = st.selectbox(
   "Select",
   ("Equity (HDFC)", "Commodities (Emkay)","Future (Emkay)","Equity (Emkay)","Nakamichi (Future)")
)
if option == 'Equity (HDFC)':
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
if option == 'Commodities (Emkay)':
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
if option == 'Future (Emkay)':
     uploaded_files2 = st.file_uploader("Choose a PDF file", accept_multiple_files=False)
     if uploaded_files2 is not None:
        df_new = pdf_to_excel_index_futures(uploaded_files2)
        df_new = df_new.fillna("")
        st.dataframe(df_new)
        csv_data = convert_df(df_new)
        btn = st.download_button(
        label="Download",
        data=csv_data,
        file_name="Future Summary.csv",
        mime="text/csv",)
if option == "Equity (Emkay)":
    uploaded_files3 = st.file_uploader("Choose a PDF file", accept_multiple_files=False)
    if uploaded_files3 is not None:
        df_new = pdf_to_excel_equity_mkay(uploaded_files3)
        df_new = df_new.fillna("")
        st.dataframe(df_new)
        csv_data = convert_df(df_new)
        btn = st.download_button(
        label="Download",
        data=csv_data,
        file_name="Equity Summary.csv",
        mime="text/csv",)
if option == "Nakamichi (Future)":
    uploaded_files5 = st.file_uploader("Choose a PDF file", accept_multiple_files=False)
    if uploaded_files5 is not None:
        df_new = pdf_to_excel_index_futures_nakamichi(uploaded_files5)
        df_new = df_new.fillna("")
        st.dataframe(df_new)
        csv_data = convert_df(df_new)
        btn = st.download_button(
        label="Download",
        data=csv_data,
        file_name="Equity Summary.csv",
        mime="text/csv",)