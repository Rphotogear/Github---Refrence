def get_RM_Price():
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

    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_SO = 'SO-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_PO = 'PO-'+date.today().strftime("%d-%m-%Y")+'.csv'

    #declaire cin7 and RM file
    file_cin7 = file_products
    file_RM = 'RM_products.csv'


    def get_RM_data(file_name):
        rm_products = pd.read_csv(file_name)
        URLS = rm_products['URL'].dropna()

        data = []
        for URL in URLS :
            page = requests.get(URL)
            soup = BeautifulSoup(page.text, 'html.parser')
            products = soup.find_all("div", class_="main-body")

            
            for product in products :
                name = product.select('.mb-2')[0].get_text()
                current_price = product.select('.price-with-cents')[0].get_text()
                data.append({"name": name, "current_price" : current_price, "URL" : URL})

        
        df = pd.DataFrame (data, columns = ['name', 'current_price', 'URL'])

        df['current_price'] = df['current_price'].astype(str).apply(lambda x:x.replace(',','').replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())
        df['current_price'] = pd.to_numeric(df['current_price'])
        df.rename(columns={'name': 'RM name'}, inplace=True)

        rm_price_check = pd.merge(rm_products, 
                        df, 
                        on ='URL', 
                        how ='left',
                        suffixes=('_PO', '_PI')
                        )

        rm_price_check.rename(columns={'code': 'Code'}, inplace=True)
        rm_price_check.rename(columns={'current_price': 'RM Price'}, inplace=True)
        return rm_price_check

    def cin7_NL(file_name):
        #normalise the cin7 products to make sure it shows (current special, current Scan, real replacement cost, margins)

        #read the cin7 product file

        df3 = pd.read_csv(file_name)
        df3 = df3.fillna(0)

        col = ['Supplier Code', 'Product Name','Style Code', 'Brand', 'Stock Control','Code','Retail NZD Incl', 'Wholesale NZD Excl', 'Cost NZD Excl', 'CostUSD USD Exempt',	'CostRMB CNY Exempt', 'CostAUD AUD Exempt', 'CostEUR EUR Exempt', 'Special Price', 'Special Start Date', 'Special Days', 'Average Landed Cost', 'Stock Avail', 'SOH', 'Rebate Calc', 'Scan value', 'Scan End Date1']
        df3 = df3[col]

        df3['MatchKey'] = df3['Supplier Code'].astype(str).apply(lambda x:x.replace('\n','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())


        df3['Special Start Date'] = pd.to_datetime(df3['Special Start Date'])

        df3['time_added'] = pd.to_timedelta(df3['Special Days'],unit='D')
        df3.dtypes
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

        df3['RRP Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Retail NZD Incl'] /1.15 )
        df3['Special Price Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Special Price'] /1.15 )
        df3['Current Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Current Price'] /1.15 )
        df3 = df3.round(2)
        return df3


    cin7_NR = cin7_NL(file_cin7)
    RM_data = get_RM_data(file_RM)


    cin7_compare = cin7_NR[cin7_NR['Code'].isin(RM_data['Code'])]
    cin7_compare = pd.merge(cin7_compare, 
                        RM_data, 
                        on ='Code', 
                        how ='left',
                        )


    cin7_compare['RM Price'] = cin7_compare['RM Price'].astype(str).apply(lambda x:x.replace(',','').replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())
    cin7_compare['RM Price'] = cin7_compare['RM Price'].astype(float)

    #calculate RM margin etc
    cin7_compare['RM is cheaper By ($)'] = cin7_compare['Current Price'] - cin7_compare['RM Price']
    cin7_compare['RM Margin'] = 1 - cin7_compare['Real Replacement Cost'] / (cin7_compare['RM Price'] /1.15 )

    cin7_compare = cin7_compare.drop(columns=['Product Name_y','CostUSD USD Exempt', 'CostRMB CNY Exempt','CostAUD AUD Exempt','CostEUR EUR Exempt','Rebate Calc','time_added','Special Ends in','Scan Ends in','temp_cost','cost_after scan'])
    cin7_compare = cin7_compare.round(2)
    cin7_compare.to_csv('RM Price Check - '+date.today().strftime("%d-%m-%Y")+'.csv')

    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = "RM Price Check - "+date.today().strftime("%d-%m-%Y")
    body = "Daily Report Email"
    sender_email = "mail@photogear.co.nz"
    receiver_email = "jay@photogear.co.nz, harry@photogear.co.nz"
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


    f1 = 'RM Price Check - '+date.today().strftime("%d-%m-%Y")+'.csv'

    add_file(f1)


    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_RM_Price()