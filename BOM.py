import numpy as np
import pandas as pd
from pandas import json_normalize 
import matplotlib.pyplot as plt
import requests
import json
import time as time
from datetime import date
from datetime import timedelta

def get_BOM_function():

    def get_BOM():
        

        #get Sales Orders
        url = "https://api.cin7.com/api/v1/BomMasters"

        page = 1
        new_results = True
        orders = []
        #while new_results:
        querystring = {"page":page,"rows":"250"}

        while new_results:
            querystring = {"page":page,"rows":"250"}
            headers = {
            'authorization': "Basic UGhvdG9nZWFyMk5aOjU1NTI3YjBmNzJjMDRjNjliNWZiMzI3NDliMWYxYzQy",
            'cache-control': "no-cache",
            'postman-token': "d57962dc-1d76-6652-ec65-3765f5feb6ba"
            }

            r = requests.request("GET", url, headers=headers, params=querystring)
            new_results = r.json()
            orders.extend(new_results)
            page += 1
            time.sleep(1/3)

        df2 = pd.DataFrame.from_dict(orders)
        


        return df2

    def get_BOM_products (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["components"])

        i = 1
        dfy = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfy = dfy.append(pd.json_normalize(dfx[i]))
            i+=1

        dfy = dfy.dropna(subset=['id'])
        return dfy

    df = get_BOM()
    dfp = pd.json_normalize(df["product"])
    file_products = 'ProductExport-'+date.today().strftime("%d-%m-%Y")+'.csv'
    df_cin7_product = pd.read_csv(file_products, usecols=['Code'])
    dfp = dfp[dfp['code'].isin(df_cin7_product['Code'])]

    df_a = get_BOM_products (dfp)
    df_b = dfp.merge(df_a, how='left', left_on='id', right_on='productId')
    df_b = df_b.dropna()

    dfp = dfp.dropna()

    df_BOM_master = dfp[['id','code','name']]
    df_BOM_master = df_BOM_master.rename(columns={'id':'BOM_id','code':'BOM_code','name':'BOM_name'})

    df_BOM_comp = df_a[['productId','code','name','qty']]
    df_BOM_comp = df_BOM_comp.rename(columns={'code':'component_code','name':'component_name','qty':'component_qty'})

    def cin7_NL(file_name):
            #normalise the cin7 products to make sure it shows (current special, current Scan, real replacement cost, margins)

            #read the cin7 product file
            col = ['Supplier Code', 'Product Name','Style Code', 'Brand', 'Stock Control','Code','Retail NZD Incl', 'Wholesale NZD Excl', 'Cost NZD Excl', 'CostUSD USD Exempt',	'CostRMB CNY Exempt', 'CostAUD AUD Exempt', 'CostEUR EUR Exempt', 'Special Price', 'Special Start Date', 'Special Days', 'Average Landed Cost', 'Stock Avail', 'SOH', 'Rebate Calc', 'Scan value', 'Scan End Date1', 'Name Promo','Description Promo']


            df3 = pd.read_csv(file_name, usecols=col)
            df3 = df3.fillna(0)

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
    cin7_NR = cin7_NL(file_products)

    cin7_NR_a = cin7_NR[['Code','Retail NZD Incl','Real Replacement Cost', 'Current Price','Is Current Special?','Special Ends in','Special Start Date','Special Days','Special End Date', 'Name Promo','Description Promo']]

    # create a list of conditions to separate the current scans
    conditions1 = [
        (cin7_NR_a['Special Ends in'] > 0),
        (cin7_NR_a['Special Ends in'] <= 0)
    ]

    values1 = [cin7_NR_a['Special Ends in'], 0]
    cin7_NR_a['Special Ends in'] = np.select(conditions1, values1)
    cin7_NR_a = cin7_NR_a.rename(columns={'Current Price':'Special Price'})

    cin7_NR_a.set_index("Code", inplace=True)
    df_BOM_comp.reset_index(inplace=True)
    df_BOM_comp.set_index("productId", inplace=True)
    df_BOM_master.set_index("BOM_id", inplace=True)

    df_BOM_comp['BOM_code'] = df_BOM_comp.index.map(df_BOM_master['BOM_code'])
    df_BOM_comp['BOM_name'] = df_BOM_comp.index.map(df_BOM_master['BOM_name'])


    df_BOM_comp.set_index("BOM_code", inplace=True)

    df_BOM_comp['BOM_Is_On_Special?'] = df_BOM_comp.index.map(cin7_NR_a['Is Current Special?'])
    df_BOM_comp['BOM_RRP'] = df_BOM_comp.index.map(cin7_NR_a['Retail NZD Incl'])
    df_BOM_comp['BOM_Special_Price'] = df_BOM_comp.index.map(cin7_NR_a['Special Price'])
    df_BOM_comp['BOM_Special_Start_Date'] = df_BOM_comp.index.map(cin7_NR_a['Special Start Date'])
    df_BOM_comp['BOM_Special_Days'] = df_BOM_comp.index.map(cin7_NR_a['Special Days'])
    df_BOM_comp['BOM_Special_End_Date'] = df_BOM_comp.index.map(cin7_NR_a['Special End Date'])

    df_BOM_comp.reset_index(inplace=True)
    df_BOM_comp.set_index("component_code", inplace=True)


    df_BOM_comp['Should have Name promo'] = df_BOM_comp.index.map(cin7_NR_a['Name Promo'])
    df_BOM_comp['Description Promo'] = df_BOM_comp.index.map(cin7_NR_a['Description Promo'])








    df_BOM_comp.reset_index(inplace=True)


    df_BOM_comp = df_BOM_comp[['BOM_code','BOM_name','BOM_Is_On_Special?','BOM_RRP','BOM_Special_Price','BOM_Special_Start_Date','BOM_Special_Days','BOM_Special_End_Date','component_code','component_name','component_qty','Should have Name promo','Description Promo']]

    df_BOM_comp.set_index("component_code", inplace=True)

    df_BOM_comp['component_Is_On_Special?'] = df_BOM_comp.index.map(cin7_NR_a['Is Current Special?'])
    df_BOM_comp['component_RRC'] = df_BOM_comp.index.map(cin7_NR_a['Real Replacement Cost'])
    df_BOM_comp['component_RRP'] = df_BOM_comp.index.map(cin7_NR_a['Retail NZD Incl'])
    df_BOM_comp['component_Special_Price'] = df_BOM_comp.index.map(cin7_NR_a['Special Price'])
    df_BOM_comp['component_Special_Start_Date'] = df_BOM_comp.index.map(cin7_NR_a['Special Start Date'])
    df_BOM_comp['component_Special_Days'] = df_BOM_comp.index.map(cin7_NR_a['Special Days'])
    df_BOM_comp['component_Special_End_Date'] = df_BOM_comp.index.map(cin7_NR_a['Special End Date'])
    df_BOM_comp['component_total_RRC'] = df_BOM_comp['component_RRC'] * df_BOM_comp['component_qty']
    df_BOM_comp['component_total_RRP'] = df_BOM_comp['component_RRP'] * df_BOM_comp['component_qty']
    df_BOM_comp['component_total_Special_Price'] = df_BOM_comp['component_Special_Price'] * df_BOM_comp['component_qty']
    df_BOM_comp['component_Special Ends in'] = df_BOM_comp.index.map(cin7_NR_a['Special Ends in'])
    df_BOM_comp['component_Special Ends in'].mask(df_BOM_comp['component_Special Ends in'] == 0, 1500, inplace=True)


    df_BOM_comp.sort_values(by=['BOM_code'], inplace=True)
    df_BOM_comp = df_BOM_comp.dropna(subset=['BOM_code'])

    df_BOM_comp.reset_index(inplace=True)

    df_BOM_comp_inactive = df_BOM_comp[~df_BOM_comp['component_code'].isin(df_cin7_product['Code'])]
    df_BOM_comp_inactive.to_csv('BOM with inative component - '+date.today().strftime("%d-%m-%Y")+'.csv')

    df_BOM_comp_active = df_BOM_comp[df_BOM_comp['component_code'].isin(df_cin7_product['Code'])]
    df_BOM_comp_active = df_BOM_comp_active[~df_BOM_comp_active['BOM_code'].isin(['DLEBOX100','DLEBOX1200','DLEBOX300','DLEBOX50','DLEBOX600','DLEBOX900'])]






    df_name_promo = df_BOM_comp_active[['BOM_code',	'BOM_name','Should have Name promo', 'Description Promo']]
    df_name_promo = df_name_promo[df_name_promo['Should have Name promo'] != 0]
    df_name_promo.drop_duplicates(inplace=True)
    df_name_promo.set_index('BOM_code', inplace=True)
    df_name_promo['Name Promo'] = df_name_promo.index.map(cin7_NR_a['Name Promo'])
    df_name_promo.to_csv('Name Promo Check - '+date.today().strftime("%d-%m-%Y")+'.csv')



    
    
    n = df_BOM_comp_active['component_Is_On_Special?'] == "Current Special"
    df_BOM_comp_active['BOM Should Be On Special'] = np.where((n),'Yes','No')


    list_BOM_should_be_on_special = df_BOM_comp_active[df_BOM_comp_active['BOM Should Be On Special'].isin(['Yes'])]
    list_BOM_should_be_on_special =  list_BOM_should_be_on_special[['BOM_code']]
    df_BOM_should_be_on_special = df_BOM_comp_active[df_BOM_comp_active['BOM_code'].isin(list_BOM_should_be_on_special['BOM_code'])]
    df_BOM_should_not_be_on_special = df_BOM_comp_active[~df_BOM_comp_active['BOM_code'].isin(list_BOM_should_be_on_special['BOM_code'])]





    table_BOM_should_not_be_on_special = pd.pivot_table(df_BOM_should_not_be_on_special, values=['BOM_RRP', 'component_total_RRC','component_total_RRP'], index=['BOM_code','BOM_name'],
                        aggfunc={'BOM_RRP': np.mean,
                                'component_total_RRC': np.sum,'component_total_RRP': np.sum})
    table_BOM_should_not_be_on_special['New BOM_RRP'] = (table_BOM_should_not_be_on_special['component_total_RRP']*0.99).round(0)
    table_BOM_should_not_be_on_special['New BOM_RRP - Change'] = table_BOM_should_not_be_on_special['New BOM_RRP'] - table_BOM_should_not_be_on_special['BOM_RRP']
    table_BOM_should_not_be_on_special['New BOM_RRP Margin'] = (1-(table_BOM_should_not_be_on_special['component_total_RRC']*1.15/table_BOM_should_not_be_on_special['New BOM_RRP'])).round(2)


    table_BOM_should_not_be_on_special.reset_index(inplace=True)

    table_BOM_should_not_be_on_special.set_index("BOM_code", inplace=True)


    df_BOM_comp_active = df_BOM_comp_active[['BOM_code','BOM_Is_On_Special?','BOM_Special_Price','BOM_Special_Start_Date','BOM_Special_Days','BOM_Special_End_Date']]

    df_BOM_comp_active.drop_duplicates(inplace=True)
    df_BOM_comp_active.set_index("BOM_code", inplace=True)
    
    table_BOM_should_not_be_on_special['BOM_Is_On_Special?'] = table_BOM_should_not_be_on_special.index.map(df_BOM_comp_active['BOM_Is_On_Special?'])
    table_BOM_should_not_be_on_special['BOM_Special_Price'] = table_BOM_should_not_be_on_special.index.map(df_BOM_comp_active['BOM_Special_Price'])
    table_BOM_should_not_be_on_special['BOM_Special_Start_Date'] = table_BOM_should_not_be_on_special.index.map(df_BOM_comp_active['BOM_Special_Start_Date'])
    table_BOM_should_not_be_on_special['BOM_Special_Days'] = table_BOM_should_not_be_on_special.index.map(df_BOM_comp_active['BOM_Special_Days'])
    table_BOM_should_not_be_on_special['BOM_Special_End_Date'] = table_BOM_should_not_be_on_special.index.map(df_BOM_comp_active['BOM_Special_End_Date'])
    
    table_BOM_should_not_be_on_special.reset_index(inplace=True)




    table_BOM_should_not_be_on_special = table_BOM_should_not_be_on_special[['BOM_code','BOM_name',	'New BOM_RRP','BOM_RRP','BOM_Is_On_Special?','BOM_Special_Price','BOM_Special_Start_Date','BOM_Special_Days','BOM_Special_End_Date','component_total_RRC','component_total_RRP','New BOM_RRP - Change','New BOM_RRP Margin']]

    table_BOM_should_not_be_on_special.to_csv('BOM_should_not_be_on_special - '+date.today().strftime("%d-%m-%Y")+'.csv')

    table_BOM_should_be_on_special = pd.pivot_table(df_BOM_should_be_on_special, values=['BOM_RRP', 'component_total_RRC','component_total_RRP','component_total_Special_Price','component_Special Ends in'], index=['BOM_code','BOM_name'],
                        aggfunc={'BOM_RRP': np.mean,
                                'component_total_RRC': np.sum,'component_total_RRP': np.sum, 'component_total_Special_Price':np.sum, 'component_Special Ends in':np.min })

    table_BOM_should_be_on_special['New BOM_RRP'] = (table_BOM_should_be_on_special['component_total_RRP']*0.99).round(0)
    table_BOM_should_be_on_special['New BOM_RRP - Change'] = table_BOM_should_be_on_special['New BOM_RRP'] - table_BOM_should_be_on_special['BOM_RRP']
    table_BOM_should_be_on_special['New BOM_RRP Margin'] = (1-(table_BOM_should_be_on_special['component_total_RRC']*1.15/table_BOM_should_be_on_special['New BOM_RRP'])).round(2)
    table_BOM_should_be_on_special['New BOM_Special Price'] = (table_BOM_should_be_on_special['component_total_Special_Price']*0.99).round(0)
    table_BOM_should_be_on_special['New BOM_Special Days'] = table_BOM_should_be_on_special['component_Special Ends in']
    table_BOM_should_be_on_special['New BOM_Special Start Date'] = date.today().strftime("%d-%m-%Y")


    table_BOM_should_be_on_special['New BOM_Special Margin'] = (1-(table_BOM_should_be_on_special['component_total_RRC']*1.15/table_BOM_should_be_on_special['New BOM_Special Price'])).round(2)
    table_BOM_should_be_on_special.reset_index(inplace=True)


    table_BOM_should_be_on_special.set_index("BOM_code", inplace=True)
    
    table_BOM_should_be_on_special['BOM_Is_On_Special?'] = table_BOM_should_be_on_special.index.map(df_BOM_comp_active['BOM_Is_On_Special?'])
    table_BOM_should_be_on_special['BOM_Special_Price'] = table_BOM_should_be_on_special.index.map(df_BOM_comp_active['BOM_Special_Price'])
    table_BOM_should_be_on_special['BOM_Special_Start_Date'] = table_BOM_should_be_on_special.index.map(df_BOM_comp_active['BOM_Special_Start_Date'])
    table_BOM_should_be_on_special['BOM_Special_Days'] = table_BOM_should_be_on_special.index.map(df_BOM_comp_active['BOM_Special_Days'])
    table_BOM_should_be_on_special['BOM_Special_End_Date'] = table_BOM_should_be_on_special.index.map(df_BOM_comp_active['BOM_Special_End_Date'])
    
    table_BOM_should_be_on_special.reset_index(inplace=True)






    table_BOM_should_be_on_special = table_BOM_should_be_on_special[['BOM_code','BOM_name',	'New BOM_RRP','New BOM_Special Price','New BOM_Special Days','New BOM_Special Start Date','BOM_RRP','BOM_Is_On_Special?','BOM_Special_Price','BOM_Special_Start_Date','BOM_Special_Days','BOM_Special_End_Date','component_total_RRC','component_total_RRP','component_total_Special_Price','component_Special Ends in','New BOM_RRP - Change','New BOM_RRP Margin','New BOM_Special Margin']]
    table_BOM_should_be_on_special.to_csv('BOM_should_be_on_special - '+date.today().strftime("%d-%m-%Y")+'.csv')

def email_BOM(email_add):
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = 'BOM Report - '+date.today().strftime("%d-%m-%Y")+'.csv'
    body = "Daily Report Email"
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


    add_file('BOM with inative component - '+date.today().strftime("%d-%m-%Y")+'.csv')
    add_file('BOM_should_not_be_on_special - '+date.today().strftime("%d-%m-%Y")+'.csv')
    add_file('BOM_should_be_on_special - '+date.today().strftime("%d-%m-%Y")+'.csv')
    add_file('Name Promo Check - '+date.today().strftime("%d-%m-%Y")+'.csv')
    

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_BOM_function()
    email_BOM("jay@photogear.co.nz")
    email_BOM("jeff@photogear.co.nz")
    email_BOM("harry@photogear.co.nz")


