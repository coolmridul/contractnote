import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path
import zipfile
import shutil



list_of_columns = {
    "Integrated GST @ 18%":"g_gst",
    "SebiChrg":"g_sebi1",
    "Stamp Charges ":"g_stamp",
    "Txn":"g_trans",
    "IPFTChrg":"g_ipft_fut",
    "STT ":"g_stt",
    r"Obligation\(Payin/Out\) ": "pay_in",
    "Net Amount For NSE - FO ": "pay_net"
}

def float_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)



def pdf_to_excel_index_futures_nakamichi(abc):
    suffix = Path(abc.name).suffix
    if suffix == ".zip":
        with zipfile.ZipFile(abc, "r") as z:
            z.extractall(pwd='BVQPA2611B'.encode())
            new_abc = z.namelist()[0]
    if suffix == '.pdf':
        new_abc = abc
    final_columns = {}
    with pdfplumber.open(new_abc) as pdf:
        df1,df0 = pd.DataFrame(),pd.DataFrame()
        for j in range(len(pdf.pages)):
            page = pdf.pages[j]
            text = page.extract_text()
            line_items = []
            date_of_day = "NA"
            df = pd.DataFrame()
            inv_line_re = re.compile(r"As per Annexure 0:00:00 As per Annexure 0:00:00 (\w+) (\d{2} \w{3} \d{4}) ([BS]) (\d+(?:,\d+)*) (\d+\.\d{4}) (\d+\.\d{4}) (\d+\.\d{4}) (\d+\.\d{4}) (-?\d+\.\d{2})")

            for line in text.split('\n'):
                for key,value in list_of_columns.items():
                    pattern = key+ r"\s*:\s*-?\s*([\d,]+\.\d{2})"
                    # Find the match
                    match = re.search(pattern, text)
                    if match:
                        final_columns[value] = float(match.group(1).replace(',', ''))
                    else:
                        final_columns[value] = 0
                
                if "Trade Date :" in line:
                    date_of_day = (line.split('Trade Date :')[1]).split(' ')[0]

                line2 = inv_line_re.search(line)
                if line2:
                    name = line2.group(1)
                    expiry = line2.group(2)
                    buy_sell = line2.group(3)
                    quantity = line2.group(4).replace(",","")
                    price = line2.group(5)
                    brokerage = line2.group(6)
                    stock_original_name = name + " " +  expiry.replace(" ","") + " " + date_of_day  + " " + buy_sell
                    price_with_brokerage = line2.group(7)
                    line_items.append({"stock_name":name,"stock_original_name":stock_original_name,"expiry":expiry,"buy_sell":buy_sell,
                                    "quantity":int(quantity),"price":float(price),
                                    "brokerage":float(brokerage),
                                    "fprice":float(price_with_brokerage)})
            
            if len(line_items):
                df = pd.DataFrame(line_items)
            else:
                df['stock_name'] = "NA"
                df['stock_original_name'] = "NA"
                df['buy_sell'] = "NA"
                df['quantity'] = "NA"
                df['price'] = "NA"
                df['brokerage'] = "NA"
                df['fprice'] = "NA"
            
            df['date_of_day'] = date_of_day.replace(" ","")
            df['charges'] = abs(round(float(final_columns['pay_in']) - float(final_columns['pay_net']),2))
            
            columns_to_convert = ['g_sebi', 'g_stamp', 'g_trans', 'g_ipft_fut', 'g_stt']
            for col in columns_to_convert:
                if col in final_columns:
                    df[col] = float(final_columns[col])
                else:
                    df[col] = 0
            df['g_gst'] = df['charges'] - (df['g_sebi']+ df['g_stamp'] + df['g_trans'] + df['g_ipft_fut'] + df['g_stt'])
        
            df1 = pd.concat([df1,df],axis=0)
            
    if df1.shape[0]:
        df1 = df1.reset_index(drop=True)
        df1.drop_duplicates(inplace=True)
        # df1['lotsize'] = df1["stock_name"].apply(lambda x: collection_of_items.get(x))
        df1['lotsize'] = 1
        df1['c_stt'] = np.where(df1['buy_sell'] == 'S',df1['price']*df1['quantity'].abs()*df1['lotsize']*0.000125,0)
        df1['c_trans'] = df1['price']*df1['quantity'].abs()*df1['lotsize']*0.0000188
        df1['c_sebi'] = df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000
        df1['c_stamp'] = np.where(df1['buy_sell'] == 'B',df1['fprice']*df1['quantity'].abs()*df1['lotsize']*0.00002,0)
        df1['c_gst'] = (df1['c_trans']+df1['c_sebi']+(df1['brokerage']*df1['lotsize']*df1['quantity'].abs()))*0.18
        df1['c_ipft_fut'] = (df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000)*1.18
        df1['c_charges'] = df1['c_sebi'] + df1['c_stamp'] + df1['c_stt'] + df1['c_trans'] + df1['c_gst'] + df1['c_ipft_fut']

        cols_to_round = ['c_sebi','c_stt','c_trans','c_gst','c_charges','c_stamp','c_ipft_fut']
        df1[cols_to_round] = df1[cols_to_round].astype(float)
        df1[cols_to_round] = df1[cols_to_round].round(4)
        df1['g_charges'] = df1['g_sebi'] + df1['g_stamp'] + df1['g_stt'] + df1['g_trans'] + df1['g_gst'] + df1['g_ipft_fut']

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

        df4[['Stock', 'Expiry', 'Date', 'Buy_Sell']] = df4['stock_original_name'].str.split(' ', expand=True)
        df4['Stock_Name'] = df4['Stock'] + " " + df4['Expiry']
        df4 = df4[['Buy_Sell','Date','Stock_Name','quantity','final_price','g_charges','c_charges','c_stt']]
    else:
        df4 = pd.DataFrame()
        
    shutil.rmtree(new_abc.split("/")[0])

    # writer = pd.ExcelWriter('test.xlsx', engine='xlsxwriter')
    # df1.to_excel(writer,sheet_name='Complete Data',index=False)
    # df4.to_excel(writer,sheet_name='Short',index=False)
    # writer.save()

    return df4



# pdf_to_excel_index_futures()