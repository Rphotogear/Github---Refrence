import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from datetime import timedelta

def get_margin():



    #The raw data we get, these should be replaced by CSV download link 

    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'

    df3 = pd.read_csv(file_products)
    df3 = df3.fillna(0)

    #normalise the cin7 products to make sure it shows (current special, current Scan, real replacement cost, margins)--------------------------------------

    #read the cin7 product file



    col = ['Product Name','Style Code', 'Brand', 'Stock Control','Code','Retail NZD Incl', 'Wholesale NZD Excl', 'Cost NZD Excl', 'CostUSD USD Exempt',	'CostRMB CNY Exempt', 'CostAUD AUD Exempt', 'CostEUR EUR Exempt', 'Special Price', 'Special Start Date', 'Special Days', 'Average Landed Cost', 'Stock Avail', 'SOH','Incoming Stock', 'Rebate Calc', 'Scan value', 'Scan End Date1','Name Promo','Stock Status Out','Stock Status Custom','Custom Badge','Option 1']
    df3 = df3[col]
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
    df3['Rebate Calc'] = df3['Rebate Calc'].astype(float, errors = 'raise')
    df3['Scan value'] = df3['Scan value'].astype(float, errors = 'raise')
    m = df3['Is Current Scan?'] == "Current Scan"

    #change rebate calc from 0 to 1
    df3['Rebate Calc'].mask(df3['Rebate Calc'] == 0, 1, inplace=True)

    df3['temp_cost'] = df3['Cost NZD Excl']* df3['Rebate Calc']
    df3['cost_after scan'] = df3['Cost NZD Excl']* df3['Rebate Calc'] - df3['Scan value']

    #If the productis in current scan, then use cost after scan, which takes away the scan value, if not, just use the cost after rebate
    df3['Real Replacement Cost'] = np.where((m),df3['cost_after scan'],df3['temp_cost'])

    df3['Current Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Retail NZD Incl'] /1.15 )
    df3['Special Price Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Special Price'] /1.15 )

    conditions = [
        (df3['Special Ends in'] > 0),
        (df3['Special Ends in'] <= 0)
    ]

    values = [df3['Special Price Margin'], df3['Current Margin']]

    df3['Current Advertised Margin'] = np.select(conditions, values)

    col = ['Product Name','Style Code','Brand','Stock Control','Code','Retail NZD Incl','Wholesale NZD Excl','Cost NZD Excl','CostUSD USD Exempt','CostRMB CNY Exempt','CostAUD AUD Exempt','CostEUR EUR Exempt','Average Landed Cost', 'Special Price','Special Start Date','Special Days','Special End Date','Special Ends in', 'Rebate Calc','Scan value','Scan End Date1','Scan End Date','Scan Ends in','Is Current Special?', 'Is Current Scan?','Stock Avail','SOH','Incoming Stock','Option 1','Name Promo','Stock Status Out','Stock Status Custom','Custom Badge','Current Advertised Margin']
    df3 = df3[col]

    df3.to_csv('Daily Product Check - '+date.today().strftime("%d-%m-%Y")+'.csv')

    def send_email(address):
        import email, smtplib, ssl
        from email import encoders
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        subject = "Daily Product Check Report - "+date.today().strftime("%d-%m-%Y")
        body = "Margin, stock status custom, badge, name promo check"
        sender_email = "mail@photogear.co.nz"
        receiver_email = address
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


        add_file('Daily Product Check - '+date.today().strftime("%d-%m-%Y")+'.csv')

        text = message.as_string()

        # Log in to server using secure context and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)

    send_email('jeff@photogear.co.nz')
    send_email('harry@photogear.co.nz')
    send_email('jay@photogear.co.nz')


def run():
    get_margin()
