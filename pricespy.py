import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from datetime import date
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import tabula
import tkinter as tk
from tkinter import filedialog

def get_report():
    def get_priceSpy(shop_id):
        lst = list(np.arange(0,20000,100))
        data = pd.DataFrame()

        for i in lst:
            url = requests.get('https://classic.pricespy.co.nz/shop.php?f='+shop_id+'&lista=prod&s='+i.astype(str))
            df = pd.read_html(url.text)
            df1 = df[0]
            if df1.shape[1]<5:
                break
            df1 = df1[['Product','Shop price']]
            data = data.append(df1, ignore_index=True)
            
        data['Shop price'] = data['Shop price'].astype(str).apply(lambda x:x.replace(',','').replace('\r','').replace(' ','').replace('$','').replace('(','').replace(')','').replace('/','').lower())
        data['Shop price'] = data['Shop price'].astype(float)
        data = data.drop_duplicates(subset=['Product'])
        return data

    df_ACC = get_priceSpy('8284')
    df_RM = get_priceSpy('11232')
    df_PW = get_priceSpy('8261')
    df_PB = get_priceSpy('8246')
    df_PG = get_priceSpy('13282')

    df_ACC.set_index("Product", inplace=True)
    df_RM.set_index("Product", inplace=True)
    df_PW.set_index("Product", inplace=True)
    df_PB.set_index("Product", inplace=True)
    df_PG.set_index("Product", inplace=True)

    def cin7_NL(file_name):
            #normalise the cin7 products to make sure it shows (current special, current Scan, real replacement cost, margins)

            #read the cin7 product file

            df3 = pd.read_csv(file_name)
            df3 = df3.fillna(0)

            col = ['Supplier Code', 'Product Name','Style Code', 'Brand', 'Stock Control','Code','Retail NZD Incl', 'Wholesale NZD Excl', 'Cost NZD Excl', 'CostUSD USD Exempt','CostRMB CNY Exempt', 'CostAUD AUD Exempt', 'CostEUR EUR Exempt', 'Special Price', 'Special Start Date', 'Special Days', 'Average Landed Cost', 'Stock Avail', 'SOH', 'Rebate Calc', 'Scan value', 'Scan End Date1','PriceSpyName']
            df3 = df3[col]

            df3['MatchKey'] = df3['Supplier Code'].astype(str).apply(lambda x:x.replace('\n','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())


            df3['Special Start Date'] = pd.to_datetime(df3['Special Start Date'])

            df3['time_added'] = pd.to_timedelta(df3['Special Days'],unit='D')
            df3['Special End Date'] = df3['Special Start Date']+df3['time_added']


            df3['Special Ends in'] = (df3['Special End Date']-pd.Timestamp("today")).dt.days+1



            # create a list of conditions to separate the current specials
            conditions = [
                (df3['Special Ends in'] > 0),
                (df3['Special Ends in'] <= 0)
            ]

            values = ['Current Special', 'No Special']

            df3['Is Current Special?'] = np.select(conditions, values)

            #Deal with scans

            df3['Scan End Date'] = pd.to_datetime(df3['Scan End Date1'])
            df3['Scan Ends in'] = (df3['Scan End Date']-pd.Timestamp("today")).dt.days+1


            # create a list of conditions to separate the current scans
            conditions1 = [
                (df3['Scan Ends in'] > 0),
                (df3['Scan Ends in'] <= 0)
            ]

            values1 = ['Current Scan', 'No Scan']

            df3['Is Current Scan?'] = np.select(conditions1, values1)
            df3.head()

            df3.dtypes
            df3['Rebate Calc'] = df3['Rebate Calc'].astype(float, errors = 'raise')
            df3['Scan value'] = df3['Scan value'].astype(float, errors = 'raise')


            #change rebate calc from 0 to 1
            df3['Rebate Calc'].mask(df3['Rebate Calc'] == 0, 1, inplace=True)

            df3['temp_cost'] = df3['Cost NZD Excl']* df3['Rebate Calc']
            df3['cost_after scan'] = df3['Cost NZD Excl']* df3['Rebate Calc'] - df3['Scan value']
            
            m = df3['Is Current Scan?'] == "Current Scan"
            df3['Real Replacement Cost'] = np.where((m),df3['cost_after scan'],df3['temp_cost'])

            n = df3['Is Current Special?'] == "Current Special"
            df3['Current Price'] = np.where((n),df3['Special Price'],df3['Retail NZD Incl'])

            n = df3['Is Current Special?'] == "Current Special"
            df3['Special Price'] = np.where((n),df3['Special Price'],0)


            df3['RRP Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Retail NZD Incl'] /1.15 )
            df3['Special Price Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Special Price'] /1.15 )
            df3['Current Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Current Price'] /1.15 )
            df3 = df3.round(2)
            return df3

    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    cin7_NR = cin7_NL(file_products)
    cin7_NR_a = cin7_NR[['Code','Retail NZD Incl','Special Price','Real Replacement Cost','Current Price','Is Current Special?','Special Ends in','Special Start Date','Special Days','Special End Date','PriceSpyName','Brand','SOH']]

    # create a list of conditions to separate the current scans
    conditions1 = [
        (cin7_NR_a['Special Ends in'] > 0),
        (cin7_NR_a['Special Ends in'] <= 0)
    ]

    values1 = [cin7_NR_a['Special Ends in'], 0]
    cin7_NR_a['Special Ends in'] = np.select(conditions1, values1)

    cin7_NR_a['PriceSpyName'] = cin7_NR_a['PriceSpyName'].astype(str)
    df_cin7 =cin7_NR_a[cin7_NR_a['PriceSpyName']!='0'] 

    df_cin7.set_index("PriceSpyName", inplace=True)

    df_cin7['RM Price'] = df_cin7.index.map(df_RM['Shop price'])
    df_cin7['ACC Price'] = df_cin7.index.map(df_ACC['Shop price'])
    df_cin7['PW Price'] = df_cin7.index.map(df_PW['Shop price'])
    df_cin7['PG Price'] = df_cin7.index.map(df_PG['Shop price'])
    df_cin7['PB Price'] = df_cin7.index.map(df_PB['Shop price'])

    df_cin7 = df_cin7.fillna(99999)
    df_cin7['Min Price'] = df_cin7[['RM Price','ACC Price','PW Price','PB Price']].min(axis=1)

    df_cin7['PG-Min'] = df_cin7['Current Price'] - df_cin7['Min Price']

    conditions1 = [
        (df_cin7['PG-Min'] > 0),(df_cin7['PG-Min'] < 0), (df_cin7['PG-Min']==0)]

    values1 = ['Too High', 'Too Low','']
    df_cin7['PG is'] = np.select(conditions1, values1)

    df_cin7['Current Margin'] = (1 - (df_cin7['Real Replacement Cost']*1.15/df_cin7['Current Price'])).round(3)
    df_cin7['Margin follow Min'] = (1 - (df_cin7['Real Replacement Cost']*1.15/df_cin7['Min Price'])).round(3)

    df_cin7.to_csv('PriceSpy - ' + date.today().strftime("%d-%m-%Y")+'.csv')

def email_report(emailadd):
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = 'PriceSpy - '+date.today().strftime("%d-%m-%Y")+'.csv'
    body = "Daily Report Email"
    sender_email = "mail@photogear.co.nz"
    receiver_email = emailadd
    password = "jinbei620"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = "photogear.2@gmail.com"  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))


    def add_file(filename):
        # Open PDF file in binary mode
        with open(filename, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email    
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )

        # Add attachment to message and convert message to string
        message.attach(part)


    add_file('PriceSpy - ' + date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)


def run():
    get_report()

    email_report('jay@photogear.co.nz')
    email_report('harry@photogear.co.nz')
    email_report('sales@photogear.co.nz')
