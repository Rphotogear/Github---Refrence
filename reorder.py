import numpy as np
import pandas as pd
from datetime import date
from datetime import timedelta

def get_reorder():

    supplier_type = 'supplier_type.csv'
    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_SO = 'SO-'+date.today().strftime("%d-%m-%Y")+'.csv'
    file_PO = 'PO-'+date.today().strftime("%d-%m-%Y")+'.csv'

    def additonal_info():
        # Read the CSV data into a DataFrame
        df = pd.read_csv(file_SO, usecols=['Created Date', 'Item Code', 'Item Qty', 'Item Price', 'Item Total Discount'])

        # Convert the "Created Date" column to datetime format
        df['Created Date'] = pd.to_datetime(df['Created Date'])
        df['Last Sold Days'] = (pd.Timestamp("today")-df['Created Date']).dt.days

        # remove sales before 181 ago
        df = df.loc[df['Last Sold Days'] <= 178]
        df['Created Date'] = df['Created Date'].dt.normalize()

        df.sort_values(by=['Created Date'], inplace=True, ascending=False)
        df['Line Total'] = df['Item Price'] * df['Item Qty']
        df.loc[df['Item Qty']<0, 'Item Total Discount'] = -1 *df['Item Total Discount']

        df_disc = df.groupby(['Item Code']).sum()
        df_disc['Discount Rate'] = (df_disc['Item Total Discount'] / df_disc['Line Total']).round(2).fillna(0)

        df1 = df.pivot_table(index=pd.Grouper(key='Item Code'), 
                            columns=pd.Grouper(freq='30D', key='Created Date', origin='end'),  
                            aggfunc='sum', 
                            values='Item Qty',
                            fill_value=0)

        df1['Discount Rate'] = df1.index.map(df_disc['Discount Rate'])

        df2=df1.reset_index()   
        df2.rename(columns={df2.columns[1]: "T-180",df2.columns[2]: "T-150",df2.columns[3]: "T-120",df2.columns[4]: "T-90",df2.columns[5]: "T-60",df2.columns[6]: "T-30"}, inplace = True)
        return df2

    df_supplier_type = pd.read_csv(supplier_type)
    df1 = pd.read_csv(file_SO)
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


    #Sort PO 


    df2['Created Date'] = pd.to_datetime(df1['Created Date'])
    df2['Last Purchased Days'] = (pd.Timestamp("today")-df1['Created Date']).dt.days

    # remove PO before 181 ago
    df2 = df2.loc[df2['Last Purchased Days'] <= 180]

    # create a list of conditions to separate the sales days
    conditions = [
        (df2['Last Purchased Days'] <= 30),
        (df2['Last Purchased Days'] > 30) & (df2['Last Purchased Days'] <= 90),
        (df2['Last Purchased Days'] > 90) & (df2['Last Purchased Days'] <= 180)
    ]

    values = ['30 Days', '90 Days', '180 Days']

    df2['Purchased Range'] = np.select(conditions, values)

    # pivot table for SO-----------------------------------
    table = pd.pivot_table(df1, values='Item Qty', index=['Item Code'],
                        columns=['Sales Range'], aggfunc=np.sum)

    table = table.replace(np.nan,0)
    table['Average Monthly Sales'] = table['30 Days']*0.5+table['90 Days']*0.3+table['180 Days']*0.2
    table['30 Day Sales'] = table['30 Days']
    table['90 Day Sales'] = table["30 Days"]+table['90 Days']
    table['180 Day Sales'] = table["30 Days"]+table['90 Days']+table['180 Days']

    Sales_table = table

    # pivot table for PO ---------------------------------------
    table = pd.pivot_table(df2, values='Item Qty', index=['Item Code'],
                        columns=['Purchased Range'], aggfunc=np.sum)

    table = table.replace(np.nan,0)
    table['30 Day PO'] = table['30 Days']
    table['90 Day PO'] = table["30 Days"]+table['90 Days']
    table['180 Day PO'] = table["30 Days"]+table['90 Days']+table['180 Days']

    PO_table = table

    #Grab the PO and convert to last purchase - --------------------


    df2['BO Qty'] = df2['Item Qty'] - df2['Item Qty Moved']

    POresult = df2.groupby('Item Code').agg({'Last Purchased Days': ['min']})


    #normalise the cin7 products to make sure it shows (current special, current Scan, real replacement cost, margins)-----------------

    #read the cin7 product file


    col = ['Supplier','Product Name','Style Code', 'Brand', 'Stock Control','Code','Retail NZD Incl', 'Wholesale NZD Excl', 'Cost NZD Excl', 'CostUSD USD Exempt',	'CostRMB CNY Exempt', 'CostAUD AUD Exempt', 'CostEUR EUR Exempt', 'Special Price', 'Special Start Date', 'Special Days', 'Average Landed Cost', 'Stock Avail', 'SOH', 'Incoming Stock','Rebate Calc', 'Scan value', 'Scan End Date1']
    df3 = df3[col]

    df3['Abb'] = df3['Supplier'].str[:3] + df3['Supplier'].str[-3:] 
    df3 = df3.rename(columns={'Supplier':'Company'})
    df3.insert (0, "Order Ref", 'PO - ' + df3['Abb'] + '-' +  date.today().strftime("%d%m%y"))

    df3.insert(2,'Delivery Country','NZ')
    df3.insert(2,'Delivery Postal Code','1024')
    df3.insert(2,'Delivery City','Auckland')
    df3.insert(2,'Delivery Address 2','Mt Eden')
    df3.insert(2,'Delivery Address 1','6 Akepiro Street')
    df3.insert(2,'Delivery Company','Mt Eden Branch')


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
    m = df3['Is Current Scan?'] == "Current Scan"


    #change rebate calc from 0 to 1
    df3['Rebate Calc'].mask(df3['Rebate Calc'] == 0, 1, inplace=True)

    df3['temp_cost'] = df3['Cost NZD Excl']* df3['Rebate Calc']
    df3['cost_after scan'] = df3['Cost NZD Excl']* df3['Rebate Calc'] - df3['Scan value']

    df3['Real Replacement Cost'] = np.where((m),df3['cost_after scan'],df3['temp_cost'])

    df3['Current Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Retail NZD Incl'] /1.15 )
    df3['Special Price Margin'] = 1 - df3['Real Replacement Cost'] / (df3['Special Price'] /1.15 )
    df3['Stock Value'] = df3['Cost NZD Excl']*df3['SOH']


    #Last portion-------------------------------------------------------

    final = pd.merge(df3, Sales_table, how='left', left_on='Code', right_on='Item Code')
    final = pd.merge(final, POresult, how='left', left_on='Code', right_on='Item Code')
    final = pd.merge(final, PO_table, how='left', left_on='Code', right_on='Item Code')


    df4 = df1[["Item Code", "Last Sold Days"]]
    df4 = df4.groupby('Item Code').agg({'Last Sold Days': ['min']})
    final = pd.merge(final, df4, how='left', left_on='Code', right_on='Item Code')

    final['Stock can last'] = final['Stock Avail'] / final['Average Monthly Sales']
    final['1mth Qty'] = final['30 Day Sales'] - final['Stock Avail'] - final['Incoming Stock']
    final['3mth Qty'] = final['90 Day Sales'] - final['Stock Avail'] - final['Incoming Stock']
    final['6mth Qty'] = final['180 Day Sales'] - final['Stock Avail'] - final['Incoming Stock']


    final['180 Day Sales'].fillna(0)


    reorder = final.loc[final['180 Day Sales']>0]

    reorder['match'] = reorder['Brand'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').lower())
    reorder = pd.merge(reorder, df_st, how='left', left_on='match', right_on='match')
    reorder = reorder.round(2)

    reorder = reorder[reorder.Code != 'miscitem']
    reorder['PO#'] = 100000
    reorder['PO#'] = 'if(exact(h2,h3),g2,g2+1)'
    reorder['Order Ref'] = 'concatenate("PO-",g2)'
    reorder['Qty - Stock Turn'] = (reorder['Average Monthly Sales']*reorder['Stock turn Month']).apply(np.ceil)

    reorder = pd.merge(reorder, df_supplier_type, how='left', left_on='Company', right_on='Supplier')

    col1 = ['Type','Style Code','Stock Control','Brand_x','Order Ref','PO#','Company','Delivery Company','Delivery Address 1','Delivery Address 2','Delivery City','Delivery Postal Code','Delivery Country','Product Name','Code','Qty - Stock Turn','1mth Qty','3mth Qty','6mth Qty','Retail NZD Incl','Cost NZD Excl','CostUSD USD Exempt','CostRMB CNY Exempt','CostAUD AUD Exempt','CostEUR EUR Exempt','Stock Avail','SOH','Incoming Stock','Current Margin','Special Price Margin','30 Day Sales','90 Day Sales','180 Day Sales','30 Day PO','90 Day PO','180 Day PO','Average Monthly Sales','Stock can last','Stock turn Month','Special Price','Special Start Date','Special Days','Average Landed Cost','Rebate Calc','Scan value','Scan End Date1','Special End Date','Special Ends in','Is Current Special?','Scan End Date','Scan Ends in','Is Current Scan?','Real Replacement Cost','Stock Value']
    reorder = reorder[col1]



    reorder.sort_values(by=['Type','Company','Brand_x'], inplace=True)

    df_add = additonal_info()

    reorder = reorder.merge(df_add, how='left', left_on='Code', right_on='Item Code')

    reorder.to_csv('Reorder '+date.today().strftime("%d-%m-%Y")+'.csv')

def email_reorder(emailadd):
    #email out
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = "Reorder report - "+date.today().strftime("%d-%m-%Y")
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


    add_file('Reorder '+date.today().strftime("%d-%m-%Y")+'.csv')

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_reorder()
    email_reorder('jay@photogear.co.nz')
    email_reorder('harry@photogear.co.nz')
    email_reorder('sales@photogear.co.nz')
    email_reorder('jeff@photogear.co.nz')
