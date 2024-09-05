import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING


def float_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)

def pdf_to_excel_index_futures(abc):
    with pdfplumber.open(abc,password='AAFCN1116J') as pdf:
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
            inv_line_re = re.compile(r'(\d+)\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\s+(\d{2}:\d{2}:\d{2})\s+(\w)\s+(\w+)\s+(\w+)\s+(\d{2}/\d{2}/\d{2})\s+(Buy|Sell)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)\s+(\w)')
            for line in text.split('\n'):
                if "Integrated GST @ 18%" in line:
                    if len(line.split(' ')) == 6:
                        gst = line.split(' ')[4]
                    else:
                        gst = line.split(' ')[7]
                if "SEBI Fees" in line:
                    if len(line.split(' ')) == 4:
                        sebi = line.split(' ')[2]
                    else:
                        sebi = line.split(' ')[5]
                if "Stamp Duty" in line:
                    if len(line.split(' ')) == 4:
                        stamp = line.split(' ')[2]
                    else:
                        stamp = line.split(' ')[5]
                if "TRANS. CHARGES-FUT" in line:
                    if len(line.split(' ')) == 4:
                        transaction = line.split(' ')[2]
                    else:
                        transaction = line.split(' ')[5]
                if "IPFT Charges FUT" in line:
                    # print(line.split(' '))
                    if len(line.split(' ')) == 5:
                        ipft_fut = line.split(' ')[3]
                    else:
                        ipft_fut = line.split(' ')[6]
                if "STT" in line:
                    if len(line.split(' ')) == 3:
                        ctt = line.split(' ')[1]
                    else:
                        ctt = line.split(' ')[4]
                if "PayIn/Payout Obligation" in line:
                    if len(line.split(' ')) == 4:
                        pay_in = line.split(' ')[2]
                    else:
                        pay_in = line.split(' ')[5]
                if "Net amount Receivable(-) / Payable(+) By Client" in line:
                    if len(line.split(' ')) == 9:
                        pay_net = line.split(' ')[7]
                    else:
                        pay_net = line.split(' ')[10]
                if "Trade Date" in line:
                    date_bill = line.split(" ")[3]
                
                line2 = inv_line_re.search(line)
                if line2:
                    name = line2.group(7)
                    expiry = line2.group(8)
                    buy_sell = line2.group(9)
                    number = line2.group(3)
                    quantity = line2.group(10)
                    price = line2.group(11)
                    brokerage = line2.group(12)
                    stock_original_name = name + " " + expiry + " " + date_bill + " " + buy_sell
                    price_with_brokerage = line2.group(13)
                    line_items.append({"stock_name":name,"number":number,"stock_original_name":stock_original_name,"expiry":expiry,"buy_sell":buy_sell,
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
    df1['c_stt'] = np.where(df1['buy_sell'] == 'Sell',df1['price']*df1['quantity'].abs()*df1['lotsize']*0.000125,0)
    df1['c_trans'] = df1['price']*df1['quantity'].abs()*df1['lotsize']*0.0000188
    df1['c_sebi'] = df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000
    df1['c_stamp'] = np.where(df1['buy_sell'] == 'Buy',df1['fprice']*df1['quantity'].abs()*df1['lotsize']*0.00002,0)
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
    df4[['Stock', 'Expiry', 'Date', 'Buy_Sell']] = df4['stock_original_name'].str.split(' ', expand=True)

    df4 = df4[['Buy_Sell','Date','Stock','Expiry','quantity','final_price','g_charges','c_charges']]

    # writer = pd.ExcelWriter('test.xlsx', engine='xlsxwriter')
    # df1.to_excel(writer,sheet_name='Complete Data',index=False)
    # df4.to_excel(writer,sheet_name='Short',index=False)
    # writer.save()

    return df4



# pdf_to_excel_index_futures()