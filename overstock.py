from email.policy import default
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from datetime import timedelta

def get_overstock():



    #The raw data we get, these should be replaced by CSV download link 

    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_SO = 'SO-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_PO = 'PO-'+date.today().strftime("%d-%m-%Y")+'.csv'


    df1 = pd.read_csv(file_SO)
    #Define the columns required
    df1 = df1[["Created Date", "Branch", "Item Code", "Item Name", "Item Qty"]]

    df2 = pd.read_csv(file_PO)
    df2['Created Date'] = pd.to_datetime(df2['Created Date'])

    df3 = pd.read_csv(file_products)
    df3 = df3.fillna(0)

    df_st = pd.read_csv('stockturn.csv')

    df_st['match'] = df_st['Brand'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())

    #remove unwanted products
    remove_words = ['Demo','demo', 'DEMO','rental','Rental','RENTAL','RENTL','misc','Misc','MISC','Shipping']

    for remove_word in remove_words:
        df3 = df3[~df3 ['Product Name'].str.contains(remove_word)]


    df1['Created Date'] = pd.to_datetime(df1['Created Date'])
    df1['Last Sold Days'] = (pd.Timestamp("today")-df1['Created Date']).dt.days

    # remove sales before 181 ago
    df1 = df1.loc[df1['Last Sold Days'] <= 180]

    # create a list of conditions to separate the sales days
    conditions = [
        (df1['Last Sold Days'] <= 30),
        (df1['Last Sold Days'] > 30) & (df1['Last Sold Days'] <= 90),
        (df1['Last Sold Days'] > 90) & (df1['Last Sold Days'] <= 180)
    ]

    values = ['30 Days', '90 Days', '180 Days']

    df1['Sales Range'] = np.select(conditions, values)

    # pivot table ------------------------------------------------------
    table = pd.pivot_table(df1, values='Item Qty', index=['Item Code'],
                        columns=['Sales Range'], aggfunc=np.sum)

    table = table.replace(np.nan,0)
    table['Average Monthly Sales'] = table['30 Days']*0.5+table['90 Days']*0.3+table['180 Days']*0.2
    table['Average Monthly Sales (SA)'] = (table['30 Days']+table['90 Days']+table['180 Days'])/6
    table['30 Day Sales'] = table['30 Days']
    table['90 Day Sales'] = table["30 Days"]+table['90 Days']
    table['180 Day Sales'] = table["30 Days"]+table['90 Days']+table['180 Days']

    Sales_table = table


    #Grab the PO and convert to last purchase------------------------


    df2['BO Qty'] = df2['Item Qty'] - df2['Item Qty Moved']
    df2 = df2.loc[df2['Item Qty Moved'] != 0]


    df2['Last Purchase Days'] = (pd.Timestamp("today")-df1['Created Date']).dt.days

    POresult = df2.groupby('Item Code').agg({'Last Purchase Days': ['min']})


    #normalise the cin7 products to make sure it shows (current special, current Scan, real replacement cost, margins)--------------------------------------

    #read the cin7 product file


    col = ['Product Name','Style Code', 'Brand', 'Stock Control','Code','Retail NZD Incl', 'Wholesale NZD Excl', 'Cost NZD Excl', 'CostUSD USD Exempt',	'CostRMB CNY Exempt', 'CostAUD AUD Exempt', 'CostEUR EUR Exempt', 'Special Price', 'Special Start Date', 'Special Days', 'Average Landed Cost', 'Stock Avail', 'SOH', 'Rebate Calc', 'Scan value', 'Scan End Date1']
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
    df3.head()

    df3.dtypes
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
    df3['Stock Value'] = df3['Cost NZD Excl']*df3['SOH']


    #final stage-----------------------------------

    final = pd.merge(df3, Sales_table, how='left', left_on='Code', right_on='Item Code')
    final = pd.merge(final, POresult, how='left', left_on='Code', right_on='Item Code')


    df4 = df1[["Item Code", "Last Sold Days"]]
    df4 = df4.groupby('Item Code').agg({'Last Sold Days': ['min']})
    final = pd.merge(final, df4, how='left', left_on='Code', right_on='Item Code')

    final['Stock can last'] = final['Stock Avail'] / final['Average Monthly Sales']
    final['Stock can last (SA)'] = final['Stock Avail'] / final['Average Monthly Sales (SA)']


    final.to_csv('final.csv')
    
    # Stock avail > 0 or special days = 999------------------------------------

    overstock = final.loc[(final['Stock Avail'] > 0) | (final['Special Days'] == 999) ]

    #

    overstock['match'] = overstock['Brand'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())
    overstock = pd.merge(overstock, df_st, how='left', left_on='match', right_on='match')
    overstock = overstock.drop(columns=['CostUSD USD Exempt', 'CostRMB CNY Exempt','CostAUD AUD Exempt','CostEUR EUR Exempt','time_added','temp_cost','cost_after scan','180 Days','30 Days','90 Days'])
    overstock = overstock.round(2)
    overstock = overstock.fillna(0)

    overstock['Last Purchase Days', 'min'] = np.select([overstock['Last Purchase Days', 'min']==0],['180'],default=overstock['Last Purchase Days', 'min'])

    #calculate qty to remove

    overstock['Qty to clear'] = (overstock['Stock can last'] - overstock['Stock turn Month'])* overstock['Average Monthly Sales']
    overstock['Qty to clear'] = overstock['Qty to clear'].round(0)
    overstock['Qty to clear'] = np.select([(overstock['Qty to clear']==0)&(overstock['SOH']>0)], [overstock['SOH']],default=overstock['Qty to clear'])

    overstock['Qty to clear (SA)'] = (overstock['Stock can last (SA)'] - overstock['Stock turn Month'])* overstock['Average Monthly Sales (SA)']
    overstock['Qty to clear (SA)'] = overstock['Qty to clear (SA)'].round(0)
    overstock['Qty to clear (SA)'] = np.select([(overstock['Qty to clear (SA)']==0)&(overstock['SOH']>0)], [overstock['SOH']],default=overstock['Qty to clear (SA)'])


    overstock = overstock.drop(columns=['Brand_y', 'match'])

    #move SOH to last col

    new_col = overstock.pop('SOH')
    overstock.insert(overstock.shape[1], 'SOH', new_col)
    print(overstock.shape)

    #calculate clearance prices

    overstock['T1 clearance price'] = (overstock['Retail NZD Incl'] - overstock['Average Landed Cost']*1.15) *.66 + overstock['Cost NZD Excl']*1.15
    overstock['T2 clearance price'] = (overstock['Retail NZD Incl'] - overstock['Average Landed Cost']*1.15) *.33 + overstock['Cost NZD Excl']*1.15
    overstock['T3 clearance price'] = (overstock['Retail NZD Incl'] - overstock['Average Landed Cost']*1.15) *.0 + overstock['Cost NZD Excl']*1.15*1.02

    overstock = overstock.round(2)
    overstock = overstock[overstock.Code != 'miscitem']
    overstock = overstock[overstock.Brand_x != 'Packaging']

    overstock.sort_values(by=['Brand_x','Stock can last'], inplace=True)
    overstock.to_csv('Overstock '+date.today().strftime("%d-%m-%Y")+'.csv')
    
    #email out
def email_overstock(emailadd):
    import email, smtplib, ssl
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = "Overstock report - "+date.today().strftime("%d-%m-%Y")
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


    add_file('Overstock '+date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_overstock()

    email_overstock('jay@photogear.co.nz')
    email_overstock('harry@photogear.co.nz')
    email_overstock('sales@photogear.co.nz')
