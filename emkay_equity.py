import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING


def float_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)

def pdf_to_excel_equity_mkay(abc):
    with pdfplumber.open(abc) as pdf:
        df1 = pd.DataFrame()
        #len(pdf.pages)
        for j in range(len(pdf.pages)):
            page = pdf.pages[j]
            text = page.extract_text()
            # print(text)
            pay_in = 0
            pay_net = 0
            gst = 0
            sebi = 0
            stamp = 0
            transaction = 0
            ctt = 0
            ipft = 0
            ipft_fut = 0
            date_bill = "NA"
            line_items = []
            df = pd.DataFrame()
            inv_line_re = re.compile(r'^(\d{8})\s+(\d{2}:\d{2}:\d{2})\s+(\d{8})\s+(\d{2}:\d{2}:\d{2})\s+([A-Z\s]+?)\s+(Buy|Sell)\s+(-?\d+)\s+(\d+\.\d{5})\s+(\d+\.\d{6})\s+(\d+\.\d{5})\s+(-?\d+\.\d{2})\s+([A-Z])$')

            for line in text.split('\n'):
                if "Integrated GST @ 18%" in line:
                    if len(line.split(' ')) == 9:
                        gst = line.split(' ')[4]
                if "SEBI Fees" in line:
                    if len(line.split(' ')) == 7:
                        sebi = line.split(' ')[2]
                if "Stamp Duty" in line:
                    if len(line.split(' ')) == 7:
                        stamp = line.split(' ')[2]
                if "TRANSACTION CHARGES" in line:
                    if len(line.split(' ')) == 7:
                        transaction = line.split(' ')[2]
                if "IPFT Charges" in line:
                    # print(line.split(' '))
                    if len(line.split(' ')) == 7:
                        ipft_fut = line.split(' ')[2]
                if "S. T. T." in line:
                    if len(line.split(' ')) == 8:
                        ctt = line.split(' ')[3]
                if "PayIn/Payout Obligation" in line:
                    if len(line.split(' ')) == 7:
                        pay_in = line.split(' ')[2]
                if "Net amount Receivable(-) / Payable(+) By Client" in line:
                    if len(line.split(' ')) == 12:
                        pay_net = line.split(' ')[7]
                if "Trade Date" in line:
                    date_bill = line.split(" ")[3]
                
                line2 = inv_line_re.search(line)
                if line2:
                    name = line2.group(5)
                    # expiry = line2.group(8)
                    buy_sell = line2.group(6)
                    number = line2.group(3)
                    quantity = line2.group(7)
                    price = line2.group(8)
                    brokerage = line2.group(9)
                    stock_original_name = name + "," + date_bill + "," + buy_sell
                    price_with_brokerage = line2.group(10)
                    line_items.append({"stock_name":name,"number":number,"stock_original_name":stock_original_name,
                                       "buy_sell":buy_sell,"quantity":int(quantity),"price":float(price),
                                       "brokerage":float(brokerage),"fprice":float(price_with_brokerage)})
            
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
            
            df['date_of_day'] = date_bill
            # df['page_number'] = j
            df['charges'] = round(float(pay_net) - float(pay_in),2)
            df['g_gst'] = float(gst)
            df['g_sebi'] = float(sebi)
            df['g_stamp'] = float(stamp)
            df['g_trans'] = float(transaction)
            df['g_ipft_fut'] = float(ipft_fut)
            df['g_stt'] = float(ctt)

        
            df1 = pd.concat([df1,df],axis=0)
    
    df1 = df1.reset_index(drop=True)
    df1.drop_duplicates(inplace=True)
    # df1['lotsize'] = df1["stock_name"].apply(lambda x: collection_of_items.get(x))
    df1['lotsize'] = 1
    df1['c_stt'] = np.where(df1['buy_sell'] == 'Sell',df1['price']*df1['quantity'].abs()*df1['lotsize']*0.001,0)
    df1['c_trans'] = df1['price']*df1['quantity'].abs()*df1['lotsize']*0.0000322
    df1['c_sebi'] = df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000
    df1['c_stamp'] = np.where(df1['buy_sell'] == 'Buy',df1['fprice']*df1['quantity'].abs()*df1['lotsize']*0.00015,0)
    df1['c_gst'] = (df1['c_trans']+df1['c_sebi']+(df1['brokerage']*df1['lotsize']*df1['quantity'].abs()))*0.18
    df1['c_ipft_fut'] = (df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000)*1.18
    df1['c_charges'] = df1['c_sebi'] + df1['c_stamp'] + df1['c_stt'] + df1['c_trans'] + df1['c_gst'] + df1['c_ipft_fut']

    # df1['c_stamp'] = df1['c_stamp'].apply(float_to_decimal)
    # df1['c_stamp'] = df1['c_stamp'].map(lambda x: x.quantize(Decimal('0.1'), ROUND_CEILING))

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
         'g_charges': 'mean'
         }).reset_index()
    
    df4['final_price'] = df4['try']/df4['quantity']
    df4 = df4.drop(['try'],axis=1)
    print(df4['stock_original_name'])
    df4[['Stock', 'Date', 'Buy_Sell']] = df4['stock_original_name'].str.split(',', expand=True)

    df4 = df4[['Buy_Sell','Date','Stock','quantity','final_price','g_charges','c_charges']]

    # writer = pd.ExcelWriter('test.xlsx', engine='xlsxwriter')
    # df1.to_excel(writer,sheet_name='Complete Data',index=False)
    # df4.to_excel(writer,sheet_name='Short',index=False)
    # writer.save()

    return df4



# pdf_to_excel_equity_mkay()