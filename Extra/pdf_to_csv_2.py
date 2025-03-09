import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from itertools import repeat
from copy import copy


# final_columns = {}
# def float_to_decimal(value):
#     return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)

def pdf_to_excel_equity_mkay():
    with pdfplumber.open('NOD.PDF') as pdf:
        for j in range(len(pdf.pages)):
            page = pdf.pages[j]
            table = page.extract_table()
            if table:
            # Replace None (blank cells) with 'NA'
                processed_table = [[cell if cell is not None else 'NA' for cell in row] for row in table]
                print(processed_table)
            else:
                print("No table found on this page.")
            print(table)

        # df1,df0 = pd.DataFrame(),pd.DataFrame()
        # full_text = ""
        # for j in range(len(pdf.pages)):
        #     page = pdf.pages[j]
        #     text = page.extract_text()
        #     if text:
        #         full_text += text.replace(" ", ",")
        #     # print(page)
        #     print(full_text)
        #     line_items = []
        #     df = pd.DataFrame()

# pdf_to_excel_equity_mkay()