import time as time
import numpy as np
import pandas as pd
from pandas import json_normalize 
import matplotlib.pyplot as plt
import requests
import json
import time as time
import datetime
from datetime import date
import math

def get_transfer():    
    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_SO = 'SO-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_PO = 'PO-'+date.today().strftime("%d-%m-%Y")+'.csv'

    #Get the product list and get the brand for each product

    file1 = file_products
    cols_list1 = ['Code','Product Name','Brand','Retail NZD Incl','Stock Control','Stock Avail']
    df_p = pd.read_csv(file1, usecols=cols_list1)
    df_p = df_p.rename(columns={'Code':'SKU','Retail NZD Incl':'Price'})

    #remove unwanted products-----

    df_p = df_p[~df_p['Brand'].isin(['Packaging'])]

    remove_words = ['Demo','demo', 'DEMO','rental','Rental','RENTAL','RENTL','misc','Misc','MISC','Shipping']

    for remove_word in remove_words:
        df_p = df_p[~df_p ['Product Name'].str.contains(remove_word)]


    df_p = df_p.loc[df_p['Stock Avail']>1]

    #Get order for the last 90 days--------------

    file = file_SO

    start_date = (datetime.datetime.now() - datetime.timedelta(90))

    cols_list = ['Order Ref', 'Created Date', 'Branch', 'Freight Description', 'Item Code', 'Item Qty']

    df_SO = pd.read_csv(file, usecols=cols_list)
    df_SO['Created Date'] = pd.to_datetime(df_SO['Created Date'])

    df_SO_3mth = df_SO.loc[df_SO['Created Date'] > start_date]


    # create a list of conditions to identify orders that was dispatched from Alb

    conditions = [
        (df_SO_3mth['Freight Description'] == 'Click & Collect - North Shore (3/2 Tawa Drive, Albany, Auckland)'),
        (df_SO_3mth['Branch'] == 'Albany Branch')]

    values = ['Alb', 'Alb']

    df_SO_3mth['Dispatched From'] = np.select(conditions, values)

    df_SO_ratio = pd.pivot_table(df_SO_3mth, values='Item Qty', index=['Item Code'],
                        columns=['Dispatched From'], aggfunc=np.sum)

    df_SO_ratio = df_SO_ratio.rename(columns={'0':'ME'})
    df_SO_ratio = df_SO_ratio.fillna(0)
    df_SO_ratio = df_SO_ratio.rename(columns={'Item Code':'SKU'})

    df_p_s = df_p.merge(df_SO_ratio, how='left', left_on='SKU', right_on='Item Code')
    df_p_s = df_p_s.fillna(0)
    df_p_s = df_p_s.rename(columns={'ME':'ME 3mth Sales','Alb':'Alb 3mth Sales'})

    def get_stock():
        #get Stock
        url = "https://api.cin7.com/api/v1/Stock"

        page = 1
        new_results = True
        stock = []
        #while new_results:

        while new_results:
            querystring = {"rows":"250","page":page,"where":"available>0","fields":"productname,code,branchId,branchName,available"}
            headers = {
            'authorization': "Basic UGhvdG9nZWFyMk5aOjU1NTI3YjBmNzJjMDRjNjliNWZiMzI3NDliMWYxYzQy",
            'cache-control': "no-cache",
            'postman-token': "d57962dc-1d76-6652-ec65-3765f5feb6ba"
            }

            r = requests.request("GET", url, headers=headers, params=querystring)
            new_results = r.json()
            stock.extend(new_results)
            page += 1
            time.sleep(1/2)

        df1 = pd.DataFrame.from_dict(stock)

        return df1


    df_SOH = get_stock()

    df_SOH = df_SOH.loc[df_SOH['branchId'] <6]

    table = pd.pivot_table(df_SOH, values='available', index=['code'],
                        columns=['branchId'], aggfunc=np.sum)
    table = table.fillna(0)
    table = table.rename(columns={3:'Alb Avail',5:'ME Avail'})
    table = table.reindex()

    df_p_s_a1 = df_p_s.merge(table, how='left', left_on='SKU', right_on='code')

    df_transfer_ME = df_p_s_a1.loc[(df_p_s_a1['Alb Avail']>1)&(df_p_s_a1['ME Avail']==0)]
    df_transfer_ME['Alb to keep'] = (df_transfer_ME['Alb Avail']/4+0.1).round(0)
    df_transfer_ME['Code'] = df_transfer_ME['SKU']
    df_transfer_ME['Qty'] = df_transfer_ME['Alb Avail']-df_transfer_ME['Alb to keep']
    df_transfer_ME = df_transfer_ME.sort_values(by=['Brand','Product Name'])
    df_transfer_ME.to_csv('transfer Alb to ME - '+date.today().strftime("%d-%m-%Y")+'.csv')


    #For ME to Albany transfer

    #get the codes to remove from the list
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSqWJVeYKqbItf9zPxav24zd0snmQUG1NIvpGxeGYheRw_VwS5L26IX9uD7hgvMOAKHMGjpXd25K4XA/pubhtml'

    table_list = pd.read_html(url, header=1)

    # Select the first table (or change index to select a different one)
    df_remove = table_list[0]

    list_remove = df_remove['Code'].values.tolist()

    df_transfer_ALB = df_p_s_a1.loc[(df_p_s_a1['Alb Avail']==0)&(df_p_s_a1['ME Avail']>1)]
    df_transfer_ALB['Alb to keep'] = (df_transfer_ALB['ME Avail']/4+0.1).round(0)
    df_transfer_ALB['Code'] = df_transfer_ALB['SKU']
    df_transfer_ALB['Qty'] = df_transfer_ALB['Alb to keep']
    df_transfer_ALB = df_transfer_ALB.sort_values(by=['Brand','Product Name'])
    df_transfer_ALB = df_transfer_ALB.loc[~df_transfer_ALB['Code'].isin(list_remove)]

    df_transfer_ALB.to_csv('transfer ME to Alb - '+date.today().strftime("%d-%m-%Y")+'.csv')


def email_transfer(emailto):
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = 'transfer - '+date.today().strftime("%d-%m-%Y")+'.csv'
    body = "Daily Report Email"
    sender_email = "mail@photogear.co.nz"
    receiver_email = emailto
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


    add_file('transfer ME to Alb - '+date.today().strftime("%d-%m-%Y")+'.csv')
    add_file('transfer Alb to Me - '+date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_transfer()
    email_transfer('salvatore@photogear.co.nz')
    email_transfer('heather@photogear.co.nz')
    email_transfer('martin@photogear.co.nz')
    email_transfer('zhengwei@photogear.co.nz')   
    email_transfer('jay@photogear.co.nz') 
    email_transfer('jeff@photogear.co.nz') 