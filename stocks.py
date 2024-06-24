import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING

# collection_of_items = {
#     'SILVERM':5,
#     'ALUMINI': 1000
# }

def float_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)

def pdf_to_excel_equity(abc):
    with pdfplumber.open(abc) as pdf:
        df1 = pd.DataFrame()
        #len(pdf.pages)
        date_bill = "NA"
        gst = 0
        sebi = 0
        stamp = 0
        transaction = 0
        stt = 0
        for j in range(len(pdf.pages)):
            page = pdf.pages[j]
            text = page.extract_text()
            line_items = []
            df = pd.DataFrame()
            inv_line_re = re.compile(r'(\w+-\w+) (\w) (\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (-?\d+\.\d+$)')
            for line in text.split('\n'):
                if "Total GST on Transaction Charges For the Day" in line:
                    gst = float(line.split('Total GST on Transaction Charges For the Day: ',1)[1])
                if "Total Sebi Turnover Tax inc of GST on SOT For the Day**" in line:
                    sebi = float(line.split('Total Sebi Turnover Tax inc of GST on SOT For the Day**: ',1)[1])
                if "Total Stamp Duty For the Day" in line:
                    stamp = float(line.split('Total Stamp Duty For the Day: ',1)[1])
                if "Total Transaction Charges For the Day" in line:
                    transaction = float(line.split('Total Transaction Charges For the Day: ',1)[1])
                if "Total Security Transaction Tax For the Day" in line:
                    stt = float(line.split('Total Security Transaction Tax For the Day: ',1)[1])
                if "As on Date" in line:
                    date_bill = line.split(" ")[-1]
                
                line2 = inv_line_re.search(line)
                if line2:
                    security_name = line2.group(1).split('-')[0]
                    security_isin = line2.group(1).split('-')[1]
                    quantity = line2.group(3)
                    rate = line2.group(4)
                    brokerage = line2.group(5)
                    net_rate = line2.group(6)
                    gst_cess_charges = line2.group(8)
                    value = line2.group(9)
                    buy_sell = 'Buy' if float(line2.group(9)) < 0 else 'Sell'
                    line_items.append(
                        {"Date":date_bill,"Security_Name":security_name,"Security ISIN":security_isin,"buy_sell":buy_sell,
                         "quantity":int(quantity),"Rate":float(rate),"Net Rate":float(net_rate),
                         "gst_cess_charges":float(gst_cess_charges),"brokerage":brokerage,"Value":value})
            
            if len(line_items):
                df = pd.DataFrame(line_items)
        
            df1 = pd.concat([df1,df],axis=0)
    
    df1 = df1.reset_index(drop=True)
    
    # df1['g_gst'] = gst
    # df1['g_sebi'] = sebi
    # df1['g_stamp'] = stamp
    # df1['g_trans'] = transaction
    # df1['g_stt'] = stt
    df1['Value'] = df1['Value'].astype(float)
    df1['Value'] = df1['Value'].abs()
    # df1['c_stt'] = df1['c_stt'].round(2)
    df1['c_stt'] = df1['Value']*0.001
    df1['c_sebi'] = df1['Value'] * 0.000001
    df1['c_stamp'] = np.where(df1['buy_sell'] == 'Buy',df1['Value'].abs()*0.00015,0)
    
    df1['c_trans'] = df1['Value']*0.0000325
    df1['c_gst'] = (df1['c_trans']+df1['c_sebi'])*0.18 + df1['gst_cess_charges']
    df1['c_charges'] = df1['c_sebi'] + df1['c_stamp'] + df1['c_trans'] + df1['c_gst']
    
    # df1['c_stamp'] = df1['c_stamp'].apply(float_to_decimal)
    # df1['c_stamp'] = df1['c_stamp'].map(lambda x: x.quantize(Decimal('0.1'), ROUND_CEILING))

    # cols_to_round = ['c_sebi','c_stt','c_trans','c_gst','c_charges']
    # df1[cols_to_round] = df1[cols_to_round].astype(float)
    # df1['c_stamp'] = df1['c_stamp'].astype(float)
    # df1[cols_to_round] = df1[cols_to_round].round(4)
    # df1['g_charges'] = df1['g_sebi'] + df1['g_stamp'] + df1['g_stt'] + df1['g_trans'] + df1['g_gst']

    # df3 = df1.copy()
    # df3['stock_original_name'] = df3['Security_Name'] + df3['buy_sell']
    df4 = df1.groupby(['Date', 'Security_Name', 'Security ISIN', 'buy_sell'],sort=False).agg({'quantity': 'sum',
         'Value': 'sum',
         'c_charges': 'sum',
         'c_stt': 'sum'
         }).reset_index()

    df4 = df4[['Date','Security_Name','Security ISIN','buy_sell','quantity','Value','c_charges','c_stt']]
    
    df9 = pd.read_excel('stock_isin.xlsx')
    df_merged = pd.merge(df4, df9, how="left", left_on='Security ISIN',right_on='ISIN')
    df_merged = df_merged.drop(['ISIN Description','Security Type','ISIN'],axis=1)
    df_merged = df_merged[['Date','Security_Name','Security Name','Security ISIN','buy_sell','quantity','Value','c_charges','c_stt']]


    return df_merged
    # writer = pd.ExcelWriter('Stock_Summary.xlsx', engine='xlsxwriter')
    # # df1.to_excel(writer,sheet_name='Data',index=False)
    # df_merged.to_excel(writer,sheet_name='Summary',index=False)
    # writer.save()



# pdf_to_excel_equity()