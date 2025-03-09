import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
import zipfile
import io

def pdf_to_excel_contract_hdfc(file_name,password):
    # with pdfplumber.open(file_name, password=password) as pdf:
    #     tables = []
    # for page in pdf.pages:
    #     table = page.extract_table()
    #     print(table)
    #     print(pd.DataFrame(table))
    #     if table:
    #         tables.append(table)
    
    return None