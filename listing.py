def get_listing_tobedone():
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

    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_SO = 'SO-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_PO = 'PO-'+date.today().strftime("%d-%m-%Y")+'.csv'

    #Get the products with Code, name, description, SOH, incoming
    file1 = file_products
    cols_list1 = ['Style Code','Code','Brand','Product Name','Description','SOH','Incoming Stock']
    df_p = pd.read_csv(file1, usecols=cols_list1)



    df_pl_has_desc =df_p[~df_p['Description'].isnull()]
    df_pl_has_desc.to_csv('Item has desc in cin7.csv')


    #select products that doesn't have description on it => need to do listing --------
    

    df_pl =df_p[df_p['Description'].isnull()]

    #SOH >0 is top priority, SOH=0 but incoming >0, second prioty
    conditions = [
        (df_pl['SOH'] > 0),
        (df_pl['SOH'] < 1 ) & (df_pl['Incoming Stock'] >0)]

    values = [1, 2]

    df_pl['Listing priority (1=top)'] = np.select(conditions, values,3)

    #remove Packaging brands
    df_pl = df_pl[~df_pl['Brand'].isin(['Packaging'])]

    #remove demo or rental stock

    remove_words = ['Demo','demo', 'DEMO','rental','Rental','RENTAL','RENTL','misc','Misc','MISC','Shipping']

    for remove_word in remove_words:
        df_pl = df_pl[~df_pl ['Product Name'].str.contains(remove_word)]
        
    excl_products = ['BEHOLDER-GOPRO-AD',
    'x1monitor',
    'FD-U60',
    '800W HALOGEN LAMP',
    'PISEN BLB13',
    'W20RED',
    'Shipment',
    'WATER-BASE1',
    'PH-SB-OCT120',
    'N3151',
    'CONTROLCABLE-NUCLEUS',
    'CONTROLCABLE-TYPE-C',
    'AC ADAPTOR FOR S-2610',
    'AC ADAPTOR FOR S-2110',
    '33.4.ACC-SP-500-MATTE',
    'FT3950QR',
    'APU-BOWENSCOVER',
    'PL070322A',
    'C-R100',
    'C-R100G',
    'C-T30',
    'TRADE-IN',
    'PA-UC06 FOR 2630',
    'BP828', 'CG800', 'RENTAL-I-2400']

    df_pl = df_pl[~df_pl['Code'].isin(excl_products)]


    #sort 
    df_pl = df_pl.sort_values(by=['Listing priority (1=top)','Brand'])

    #add two columns
    df_pl['Category loaded'] = 'Please confirm'
    df_pl['Ref URL'] = 'Please confirm'


    df_pl.to_csv('Listing to be done '+date.today().strftime("%d-%m-%Y")+'.csv')

def email_listing(emailadd):
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
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

    subject = "Listing to be done report - "+date.today().strftime("%d-%m-%Y")
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


    add_file('Listing to be done '+date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_listing_tobedone()
    email_listing('jay@photogear.co.nz')
    email_listing('harry@photogear.co.nz')
    email_listing('sales@photogear.co.nz')
    email_listing('jeff@photogear.co.nz')
