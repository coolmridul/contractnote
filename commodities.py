import re
import pdfplumber
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
import zipfile
import io


collection_of_items = {
    'SILVERM':5,
    'ALUMINI': 1000,
    'COPPER': 2500,
    'GOLDM': 5,
    'SILVE':5
}

def float_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_CEILING)

def pdf_to_excel_commodities(abc):
    try:
        file_content = abc.read()
        if abc.name.lower().endswith('.zip'):
            # Handle ZIP file
            zip_file = zipfile.ZipFile(io.BytesIO(file_content))
            pdf_files = [f for f in zip_file.namelist() if f.lower().endswith('.pdf')]
            if not pdf_files:
                raise ValueError("No PDF found in ZIP")
            pdf_content = zip_file.read(pdf_files[0])
            pdf_file = io.BytesIO(pdf_content)
        else:
            # Handle direct PDF file
            pdf_file = io.BytesIO(file_content)
        
        # Process the PDF
        with pdfplumber.open(pdf_file, password='AAFCN1116J') as pdf:
            df1 = pd.DataFrame()
            for j in range(len(pdf.pages)):
                try:
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
                    date_bill = "NA"
                    line_items = []
                    df = pd.DataFrame()
                    # inv_line_re = re.compile(r'(\d{15})\s(\d{2}:\d{2}:\d{2})\s(\d{9})\s(\d{2}:\d{2}:\d{2})\s([A-Z])\s([A-Z]+)\s(\d{2}\/\d{2}\/\d{2})\s(Buy|Sell)\s(\d+)\s(\d+\.\d+)\s(\d+\.\d+)\s(\d+\.\d+)\s(\d+\.\d+)\s(-?\d+\.\d+)')
                    inv_line_re = re.compile(r'(\d{15})\s(\d{2}:\d{2}:\d{2})\s(\d{9})\s(\d{2}:\d{2}:\d{2})\s([A-Z])\s([A-Z]+)\s(\d{2}\/\d{2}\/\d{2})\s(Buy|Sell)\s(-?\d+)\s(\d+\.\d+)\s(\d+\.\d+)\s(\d+\.\d+)\s(\d+\.\d+)\s(-?\d+\.\d+)')

                    for line in text.split('\n'):
                        if "INTEGRATED GST @ 18%" in line:
                            gst = float(line.split('INTEGRATED GST @ 18% ',1)[1])
                        if "SEBI FEES" in line:
                            sebi = float(line.split('SEBI FEES ',1)[1])
                        if "STAMP DUTY" in line:
                            stamp = float(line.split('STAMP DUTY ',1)[1])
                        if "TRANSACTIO CHARGES" in line:
                            transaction = float(line.split('TRANSACTIO CHARGES ',1)[1])
                        if "CTT CHARGES" in line:
                            ctt = float(line.split('CTT CHARGES ',1)[1])
                        if "PayIn/Payout Obligation" in line:
                            pay_in = float(line.split('PayIn/Payout Obligation ',1)[1])
                        if "Net amount Receivable(-) | Payable(+) By Client" in line:
                            pay_net = float(line.split('Net amount Receivable(-) | Payable(+) By Client ',1)[1])
                        if "Bill Date" in line:
                            date_bill = line.split(" ")[3]
                        
                        line2 = inv_line_re.search(line)
                        if line2:
                            name = line2.group(6)
                            expiry = line2.group(7)
                            num = line2.group(3)
                            buy_sell = line2.group(8)
                            quantity = line2.group(9)
                            price = line2.group(10)
                            brokerage = line2.group(11)
                            stock_original_name = line2.group(6) + " " + line2.group(7) + " " + date_bill + " " + line2.group(8)
                            price_with_brokerage = line2.group(12)
                            line_items.append({"stock_name":name,"number":num,"stock_original_name":stock_original_name,"expiry":expiry,"buy_sell":buy_sell,
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
                    df['charges'] = round(pay_net - pay_in,2)
                    df['g_gst'] = gst
                    df['g_sebi'] = sebi
                    df['g_stamp'] = stamp
                    df['g_trans'] = transaction
                    df['g_stt'] = ctt

                
                    df1 = pd.concat([df1,df],axis=0)
                except Exception as e:
                    print(f"Error processing page {j}: {str(e)}")
                    continue
            
            if df1.empty:
                raise ValueError("No data was extracted from the PDF")
                
            df1 = df1.reset_index(drop=True)
            df1.drop_duplicates(inplace=True)
            df1['lotsize'] = df1["stock_name"].apply(lambda x: collection_of_items.get(x))
            df1['c_sebi'] = df1['price']*df1['quantity'].abs()*df1['lotsize']/1000000
            df1['c_stamp'] = np.where(df1['buy_sell'] == 'Buy',df1['fprice']*df1['quantity'].abs()*df1['lotsize']*0.00002,0)
            df1['c_stt'] = np.where(df1['buy_sell'] == 'Sell',df1['price']*df1['quantity'].abs()*df1['lotsize']*0.0001,0)
            df1['c_trans'] = df1['price']*df1['quantity'].abs()*df1['lotsize']*0.000026
            df1['c_gst'] = (df1['c_trans']+df1['c_sebi']+(df1['brokerage']*df1['lotsize']*df1['quantity'].abs()))*0.18
            df1['c_charges'] = df1['c_sebi'] + df1['c_stamp'] + df1['c_stt'] + df1['c_trans'] + df1['c_gst']
            
            df1['c_stamp'] = df1['c_stamp'].apply(float_to_decimal)
            df1['c_stamp'] = df1['c_stamp'].map(lambda x: x.quantize(Decimal('0.1'), ROUND_CEILING))

            cols_to_round = ['c_sebi','c_stt','c_trans','c_gst','c_charges']
            df1[cols_to_round] = df1[cols_to_round].astype(float)
            df1['c_stamp'] = df1['c_stamp'].astype(float)
            df1[cols_to_round] = df1[cols_to_round].round(4)
            df1['g_charges'] = df1['g_sebi'] + df1['g_stamp'] + df1['g_stt'] + df1['g_trans'] + df1['g_gst']

            df3 = df1.copy()
            df3['quantity'] = df3['quantity'].abs()
            df3['try'] = df3['quantity'] * df3['fprice']
            df4 = df3.groupby(['stock_original_name'],sort=False).agg({'try': 'sum',
                 'quantity': 'sum',
                 'c_charges': 'sum',
                 'g_charges': 'mean',
                 'lotsize':'mean'
                 }).reset_index()
            
            df4['final_price'] = df4['try']/df4['quantity']
            df4 = df4.drop(['try'],axis=1)
            df4[['Stock', 'Expiry', 'Date', 'Buy_Sell']] = df4['stock_original_name'].str.split(' ', expand=True)

            df4 = df4[['Buy_Sell','Date','Stock','Expiry','quantity','final_price','g_charges','c_charges','lotsize']]
            df4['quantity'] = df4['quantity']*df4['lotsize']
            df4 = df4.drop(['lotsize'],axis=1)
            # writer = pd.ExcelWriter('roshan.xlsx', engine='xlsxwriter')
            # df1.to_excel(writer,sheet_name='Complete Data',index=False)
            # df4.to_excel(writer,sheet_name='Short',index=False)
            # writer.save()

            return df4         
    except Exception as e:
        print(f"Error: {str(e)}")
        return None



# pdf_to_excel_commodities()