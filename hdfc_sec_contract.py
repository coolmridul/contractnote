import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
import zipfile
import io

def fix_broken_decimals(line):
    # Fix "0. 1 1" → "0.11"
    line = re.sub(r'(\d+)\.\s+(\d)\s+(\d)', r'\1.\2\3', line)
    
    # Fix "0.0 0" → "0.00"
    line = re.sub(r'(\d+\.\d)\s+(\d)', r'\1\2', line)
    
    return line

def extract_last_number(line,text_start):
    # Check if line starts with "PAY IN/PAY OUT"
    if line.startswith(text_start):
        # Find all numbers (including decimals and negative values)
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
        if numbers:
            return numbers[-1]  # Return the last number
    return None  # Return None if no match

def pdf_to_excel_contract_hdfc(file_name,password):
    result = None
    result2 = None
    line_items = []
    df = pd.DataFrame()
    with pdfplumber.open(file_name, password=password) as pdf:
        for j in range(0,len(pdf.pages)):
            page = pdf.pages[j]
            text = page.extract_text()
            
            inv_line_re = re.compile(r"^(\S+)\s+([\w&\s]+?)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)$")
            lines = text.splitlines()  # Splitting text into lines
            for k in range(len(lines) - 1):

                cleaned_text = fix_broken_decimals(lines[k])
                line2 = inv_line_re.search(cleaned_text)
                if cleaned_text == 'TRADE DATE':
                    date_bill = lines[k+1]
                
                if result == None:
                    result = extract_last_number(cleaned_text,'PAY IN/PAY OUT')
                if result2 == None:
                    result2 = extract_last_number(cleaned_text,'Net amount receivable')
                if line2:
                    security_name = line2.group(2)
                    security_isin = line2.group(1)
                    quantity = line2.group(3)
                    rate = line2.group(4)
                    net_rate = line2.group(6)
                    buy_sell = 'Buy'
                    if quantity == '0':
                        quantity = line2.group(8)
                        buy_sell = 'Sell'
                        rate = line2.group(9)
                        net_rate = line2.group(11)
                    line_items.append(
                        {"Date":date_bill,"Security_Name":security_name,"Security ISIN":security_isin,"buy_sell":buy_sell,
                            "quantity":int(quantity),"Rate":float(rate),"Net Rate":float(net_rate)})
                
        if len(line_items):
            df = pd.DataFrame(line_items)
        
        df['charges'] = float(result2) - float(result)
        
        return df

