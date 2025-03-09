import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from hdfc_sec_stocks import *
from commodities import *
from emkay_future import *
from emkay_equity import *
from nakamichi_fut import *
from hdfc_sec_contract import *
import io

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")

option = st.selectbox(
   "Select",
   ("Equity (HDFC)","Equity Contract (HDFC)", "Commodities (Emkay)","Future (Emkay)","Equity (Emkay)","Nakamichi (Future)")
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

def is_pdf_encrypted(uploaded_file):
    """Check if a PDF is encrypted using pdfplumber."""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            return False
    except Exception:
        return True

if option == 'Equity Contract (HDFC)':
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'], accept_multiple_files=False, key="equity_uploader")
    pdf_password = None

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf") or uploaded_file.name.endswith(".PDF"):
            # Check if the uploaded PDF is encrypted
            print(is_pdf_encrypted(uploaded_file))
            if is_pdf_encrypted(uploaded_file):
                pdf_password = st.text_input("This PDF is encrypted. Please enter the password:", type="password", key="pdf_password")

                # Ensure user enters a password
                if not pdf_password:
                    st.warning("Please enter the password to continue.")
                    st.stop()  # Stop execution until password is entered
            else:
                pdf_password = None  # No password needed if not encrypted
        
        # Process the file (Pass the password only if needed)
        with st.spinner('Processing your equity contract file...'):
            result = pdf_to_excel_contract_hdfc(uploaded_file, password=pdf_password)

        if result is not None:
            st.success('File processed successfully!')
            st.dataframe(result)
            
            buffer = io.BytesIO()
            result.to_excel(buffer, index=False)
            st.download_button(
                label="Download Excel file",
                data=buffer.getvalue(),
                file_name="processed_equity.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.error('Failed to process the file. Please check if the file and password are valid.')

if option == 'Commodities (Emkay)':
     uploaded_files1 = st.file_uploader("Choose a PDF or ZIP file", type=['pdf', 'zip'], accept_multiple_files=False)
     if uploaded_files1 is not None:
        try:
            with st.spinner('Processing your file...'):
                result = pdf_to_excel_commodities(uploaded_files1)
            
            if result is not None:
                st.success('File processed successfully!')
                st.dataframe(result)  # Display the processed data
                
                # Add download button for Excel
                buffer = io.BytesIO()
                result.to_excel(buffer, index=False)
                st.download_button(
                    label="Download Excel file",
                    data=buffer.getvalue(),
                    file_name="processed_data.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.error('Failed to process file. Please check if the file is valid.')
        except Exception as e:
            st.error(f'An error occurred: {str(e)}')
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