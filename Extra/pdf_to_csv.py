import re
import pdfplumber
import pandas as pd
import numpy as np

def pdf_to_excel():
    with pdfplumber.open('XR41156_tax_pnl_report.pdf') as pdf:
        df1 = pd.DataFrame()
        lst = []
        for j in range(len(pdf.pages)):
            page = pdf.pages[j]
            text = page.extract_text()
            inv_line_re = re.compile(r'(\w+-\w+) (\w) (\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (-?\d+(\.\d+)?$)')
            for line in text.split('\n'):
                data_list = line.split()
                if len(data_list) > 19:
                    option_data = {
                    "Symbol":' '.join(data_list[0:4]),
                    "Txn Type":data_list[4],
                    "Segment":data_list[5],
                    "Buy Date":' '.join(data_list[6:9]),
                    "Buy Qty":data_list[9],
                    "Buy Rate (₹)":data_list[10],
                    "Sell Date":' '.join(data_list[11:14]),
                    "Sell Qty":data_list[14],
                    "Sell Rate (₹)":data_list[15],
                    "P&L Amt (₹)":data_list[16],
                    "Total days":data_list[17],
                    "ISIN":data_list[18],
                    "Turnover (₹)":data_list[19]
                    }
                    lst.append(option_data)
        
        df1 = pd.DataFrame(lst)
        df1.to_csv('test.csv')

    return df1


# pdf_to_excel()