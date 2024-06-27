import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from itertools import repeat
from copy import copy

list_of_columns = {
    "Integrated GST @ 18%":"g_gst",
    "SEBI Fees":"g_sebi1",
    "SEBI FEES":"g_sebi2",
    "Stamp Duty":"g_stamp",
    "TRANSACTION CHARGES":"g_trans",
    "IPFT Charges":"g_ipft_fut",
    "S. T. T.":"g_stt",
    "PayIn/Payout Obligation":"pay_in",
    "Net amount Receivable(-) / Payable(+) By Client":"pay_net",
    "Trade Date :":"date_of_day",
    "Technology & Other Handling Charges":"handling_charges"
}
final_columns = {}
def float_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)

def pdf_to_excel_equity_mkay(abc):
    with pdfplumber.open(abc) as pdf:
        df1,df0 = pd.DataFrame(),pd.DataFrame()
        for j in range(len(pdf.pages)):
            page = pdf.pages[j]
            text = page.extract_text()
            line_items = []
            df = pd.DataFrame()
            inv_line_re = re.compile(r'^(\d+)\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\s+(\d{2}:\d{2}:\d{2})\s+([A-Z\s\.]+?)\s+(Buy|Sell)\s+(-?\d+)\s+(\d+\.\d{5,6})\s+(\d+\.\d{5,6})\s+(\d+\.\d{5,6})\s+(-?\d+\.\d{2})\s+([A-Z])$')

            for line in text.split('\n'):
                linesplit = line.split(' ')
                for key,value in list_of_columns.items():
                    if key in line:
                        columnsplit = key.split(' ')
                        if len(linesplit) - len(columnsplit) > 3:
                            if linesplit[len(columnsplit)] != "FUT":
                                final_columns[value] = linesplit[len(columnsplit)]
                
                line2 = inv_line_re.search(line)
                if line2:
                    name = line2.group(5)
                    buy_sell = line2.group(6)
                    number = line2.group(3)
                    quantity = line2.group(7)
                    price = line2.group(8)
                    brokerage = line2.group(9)
                    price_with_brokerage = line2.group(10)
                    line_items.append({"stock_name":name,"number":number,
                                        "buy_sell":buy_sell,"quantity":int(quantity),"price":float(price),
                                        "brokerage":float(brokerage),"fprice":float(price_with_brokerage)})
            
            
            if len(line_items):
                if 'g_sebi1' not in final_columns.keys():
                    final_columns['g_sebi1'] = 0
                if 'g_sebi2' not in final_columns.keys():
                    final_columns['g_sebi2'] = 0 
                if 'handling_charges' not in final_columns.keys():
                    final_columns['handling_charges'] = 0
                
                df0 = pd.DataFrame(line_items)
                df_9 = pd.DataFrame(final_columns, index=[0])
                df_copied = pd.concat([df_9] * len(line_items), ignore_index=True)
                df = pd.concat([df0,df_copied],axis=1)

                cols_to_round = ['g_sebi1','g_sebi2','g_stt','g_trans','g_gst','g_stamp','g_ipft_fut','pay_net','pay_in','handling_charges']
                df[cols_to_round] = df[cols_to_round].astype(float)
                df['g_sebi'] = df['g_sebi1'] + df['g_sebi2']
                df['charges'] = df['pay_net'] - df['pay_in']
                df['charges'] = df['charges'].round(2)
                df = df.drop(['g_sebi1','g_sebi2'],axis=1)
                df['stock_original_name'] = df['stock_name'] + "," + df['date_of_day'] + "," + df['buy_sell']
                df = df.reset_index(drop=True)

            
                df1 = pd.concat([df1,df],axis=0)
    
    df1 = df1.reset_index(drop=True)
    df1.drop_duplicates(inplace=True)
    # df1['lotsize'] = df1["stock_name"].apply(lambda x: collection_of_items.get(x))
    df1['lotsize'] = 1
    df1['c_stt'] = df1['price']*df1['quantity'].abs()*df1['lotsize']*0.001
    df1['c_trans'] = df1['price']*df1['quantity'].abs()*df1['lotsize']*0.0000322
    df1['c_sebi'] = df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000
    df1['c_stamp'] = np.where(df1['buy_sell'] == 'Buy',df1['fprice']*df1['quantity'].abs()*df1['lotsize']*0.00015,0)
    df1['c_gst'] = (df1['c_trans']+df1['c_sebi']+(df1['brokerage']*df1['lotsize']*df1['quantity'].abs()))*0.18
    df1['c_ipft_fut'] = (df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000)*1.18
    df1['c_charges'] = df1['c_sebi'] + df1['c_stamp'] + df1['c_stt'] + df1['c_trans'] + df1['c_gst'] + df1['c_ipft_fut']

    cols_to_round = ['c_sebi','c_stt','c_trans','c_gst','c_charges','c_stamp','c_ipft_fut','handling_charges']
    df1[cols_to_round] = df1[cols_to_round].astype(float)
    df1[cols_to_round] = df1[cols_to_round].round(4)
    # df1['g_charges'] = df1['g_sebi'] + df1['g_stamp'] + df1['g_stt'] + df1['g_trans'] + df1['g_gst'] + df1['g_ipft_fut'] + df['handling_charges']
    df1['g_charges'] = df1['charges']
    
    df3 = df1.copy()
    df3['quantity'] = df3['quantity'].abs()
    df3['try'] = df3['quantity'] * df3['fprice']
    df4 = df3.groupby(['stock_original_name'],sort=False).agg({'try': 'sum',
         'quantity': 'sum',
         'c_charges': 'sum',
         'g_charges': 'mean',
         'c_stt':'sum'
         }).reset_index()
    
    df4['final_price'] = df4['try']/df4['quantity']
    df4 = df4.drop(['try'],axis=1)
    df4[['Stock', 'Date', 'Buy_Sell']] = df4['stock_original_name'].str.split(',', expand=True)

    df4 = df4[['Buy_Sell','Date','Stock','quantity','final_price','g_charges','c_charges','c_stt']]
    df4['c_charge_wo_stt'] = df4['c_charges'] - df4['c_stt']
    # writer = pd.ExcelWriter('test.xlsx', engine='xlsxwriter')
    # df1.to_excel(writer,sheet_name='Complete Data',index=False)
    # df4.to_excel(writer,sheet_name='Short',index=False)
    # writer.save()

    return df4



# pdf_to_excel_equity_mkay()