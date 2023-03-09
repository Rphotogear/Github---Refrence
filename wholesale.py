import numpy as np
import pandas as pd
from pandas import json_normalize 
import matplotlib.pyplot as plt
import requests
import json
import time as time
from datetime import date
from datetime import timedelta

def ws_email():   
    file_name = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'

    df3 = pd.read_csv(file_name)
    df3 = df3.fillna(0)

    col = ['Brand', 'Code', 'Product Name','Style Code', 'Retail NZD Incl', 'Wholesale NZD Excl']
    df3 = df3[col]
    df4 = df3.loc[df3['Wholesale NZD Excl']>0] 


    df4['Brand'] = df4['Brand'].astype(str).apply(lambda x:x.lower())
    df4.sort_values(by=['Brand'], inplace=True)

    df4.to_csv('Photogear Price List - '+date.today().strftime("%d-%m-%Y")+'.csv')



def email_ws(email_add):
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = 'Photogear Wholesale Price List - '+date.today().strftime("%d-%m-%Y")
    body = "Please see the latest price list. \n \nPlease note, the prices might get updated regularly, so please refer to this list when you need to price for your customer.\n \nIn any case that there is an error made to the wholesale price, we will try our best to honor but we do reserve the right to change the pricing immediately without any notice.\nPlease do not reply to this email and please contact sales@photogear.co.nz if you have any questions."
    sender_email = "mail@photogear.co.nz"
    receiver_email = email_add
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


    add_file('Photogear Price List - '+date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    ws_email()

    if date.today().weekday() == 1:
        email_ws('sales@snapshot.co.nz')
        email_ws('admin@aucklandcamera.co.nz')
        email_ws('matt@cartersphotographics.co.nz')

    email_ws('jeff@photogear.co.nz')
    email_ws('kevin@progear.co.nz')
    email_ws('supplier.api@rubbermonkey.co.nz')
