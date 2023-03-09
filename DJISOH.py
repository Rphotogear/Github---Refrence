from email.policy import default
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from datetime import timedelta

def run():

    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_DJI = 'DJI SOH Report.csv'


    df1 = pd.read_csv(file_DJI)
    df1.set_index('SKU', inplace=True)


    df3 = pd.read_csv(file_products, usecols=['Brand','Supplier Code','SOH','Incoming Stock'])
    df3 = df3.fillna(0)
    df3['Brand'] = df3['Brand'].astype(str).apply(lambda x:x.replace('\n','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())

    df_cin7 = df3.loc[df3['Brand']=='dji']
    df_cin7.set_index('Supplier Code', inplace=True)

    df1['Incoming Qty'] = df1.index.map(df_cin7['Incoming Stock'])
    df1['Qty In Stock'] = df1.index.map(df_cin7['SOH'])

    df1 = df1[['Product name','Incoming Qty','Qty In Stock']]
    df1.to_csv('DJI SOH Report -'+date.today().strftime("%d-%m-%Y")+'.csv')


    import email, smtplib, ssl
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = "DJI SOH Report - "+date.today().strftime("%d-%m-%Y")
    body = "DJI SOH Report"
    sender_email = "mail@photogear.co.nz"
    receiver_email = "cody@ferntech.co.nz"
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


    add_file('DJI SOH Report -'+date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)


run()