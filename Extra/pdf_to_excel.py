import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from itertools import repeat
from copy import copy


# def pdf_to_excel_equity_mkay():
#     with pdfplumber.open('NOD.PDF') as pdf:
#         df1 = pd.DataFrame()
#         for j in range(len(pdf.pages)-1):
#             for page in pdf.pages:
#                 tables = page.extract_tables()
#                 for table in tables:
#                     for row in table:
#                         print(row)  # Print each row of the table

# pdf_to_excel_equity_mkay()

# import camelot

# pdf_path = "NOD.PDF"
# df1 = pd.DataFrame()
# tables = camelot.read_pdf(pdf_path, pages="all")
# for table in tables:
#     # print(table.df)
#     df1 = pd.concat([df1, table.df], ignore_index=True)

# df1.to_csv('nod.csv')
