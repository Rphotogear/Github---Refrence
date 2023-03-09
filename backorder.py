import numpy as np
import pandas as pd
from pandas import json_normalize 
import requests
import json
import time as time
from datetime import date
from datetime import timedelta

def get_BO_Report():
    import numpy as np
    import pandas as pd
    from pandas import json_normalize 
    import requests
    import json
    import time as time
    from datetime import date
    from datetime import timedelta


    def get_Product():
        #get Products
        url = "https://api.cin7.com/api/v1/Products"

        page = 1
        new_results = True
        products = []
        #while new_results:
        querystring = {"page":page,"rows":"250","where":"status='Public'","fields":"id, name, productOptions"}

        while new_results:
            querystring = {"page":page,"rows":"250","where":"status='Public'","fields":"id, name, productOptions"}
            headers = {
            'authorization': "Basic UGhvdG9nZWFyMk5aOjU1NTI3YjBmNzJjMDRjNjliNWZiMzI3NDliMWYxYzQy",
            'cache-control': "no-cache",
            'postman-token': "d57962dc-1d76-6652-ec65-3765f5feb6ba"
            }

            r = requests.request("GET", url, headers=headers, params=querystring)
            new_results = r.json()
            products.extend(new_results)
            page += 1
            time.sleep(1/3)

        dfp = pd.DataFrame.from_dict(products)

        return dfp

    def get_SO():
        

        #get Sales Orders
        url = "https://api.cin7.com/api/v1/SalesOrders"

        page = 1
        new_results = True
        orders = []
        #while new_results:
        querystring = {"page":page,"rows":"250","where":"DispatchedDate IS NULL","fields":"id, Stage, Status, LineItems, Reference, FirstName, LastName, Company, EstimatedDeliveryDate, InternalComments, createdDate"}

        while new_results:
            querystring = {"page":page,"rows":"250","where":"DispatchedDate IS NULL","fields":"id, Stage, Status, LineItems, Reference, FirstName, LastName, Company, EstimatedDeliveryDate, InternalComments, createdDate"}
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

        dfs = pd.DataFrame.from_dict(orders)

        #remove void
        dfs = dfs[dfs["status"].isin(['APPROVED'])]
        return dfs


    def get_SO_lineitems (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["lineItems"])

        i = 1
        dfy = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfy = dfy.append(pd.json_normalize(dfx[i]))
            i+=1

        dfs = df.drop(columns=['lineItems'])
        dfs = dfs.merge(dfy, how='left', left_on='id', right_on='transactionId')
        dfs = dfs.drop(columns=['id_x','status','parentId','productId','productOptionId','integrationRef','sort','option1','option3','styleCode','barcode','sizeCodes','unitCost','unitPrice','discount','accountCode','stockControl','stockMovements'])

        dfs = dfs.rename(columns={"option2": "PO Ref", "estimatedDeliveryDate" : "SO ETA"})
        dfs['match'] = dfs['PO Ref'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').replace('\t','').lower())
        dfs['SO ETA'] = pd.to_datetime(dfs['SO ETA'])
        #dfs['createdDate'] = pd.to_datetime(dfs['createdDate'])


        #Taking only items that has BO Qty
        dfs['BO Qty'] = dfs['qty'] - dfs['qtyShipped'] - dfs['holdingQty']
        dfs = dfs[dfs["BO Qty"]>0]

        return dfs

    def get_SOH (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["productOptions"])

        i = 1
        dfz = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfz = dfz.append(pd.json_normalize(dfx[i]))
            i+=1

        dfz = dfz[['id','code','stockOnHand','productId', 'stockAvailable']]
        dfz = dfz.rename(columns={"stockOnHand": "SOH"})
        dfz = df.merge(dfz, how='left', left_on='id', right_on='productId')
        dfz = dfz[['code','name','SOH', 'stockAvailable']]

        return dfz

    def get_PO():
        

        #get Sales Orders
        url = "https://api.cin7.com/api/v1/PurchaseOrders"

        page = 1
        new_results = True
        orders = []
        #while new_results:
        querystring = {"page":page,"rows":"250","where":"FullyReceivedDate IS NULL","fields":"id, Stage, Status, Reference, FirstName, LastName, Company, LineItems, EstimatedArrivalDate"}

        while new_results:
            querystring = {"page":page,"rows":"250","where":"FullyReceivedDate IS NULL","fields":"id, Stage, Status, Reference, FirstName, LastName, Company, LineItems, EstimatedArrivalDate"}
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

        #remove void
        df2 = df2[df2["status"].isin(['APPROVED'])]

        df2 = df2.rename(columns={"reference": "PO Ref","estimatedArrivalDate":"PO ETA","stage":"PO Stage"})
        df2 = df2[['PO Ref','PO Stage','PO ETA','lineItems']]
        df2['match'] = df2['PO Ref'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').replace('\t','').lower())
        df2['PO ETA'] = pd.to_datetime(df2['PO ETA'])


        return df2

    def get_PO_lineitems (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["lineItems"])

        i = 1
        dfy = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfy = dfy.append(pd.json_normalize(dfx[i]))
            i+=1

        dfy = dfy[dfy['qty']>0]

        return dfy

    def get_incoming(df):
        
        df = df[['code','name', 'qty']]
        table = pd.pivot_table(df, values='qty', index=['code'], aggfunc=np.sum)
        table = table.rename(columns={"qty": "incoming"})
        
        return table

    dfs = get_SO()
    dfs = get_SO_lineitems(dfs)
    df_po = get_PO()
    df_products_all = get_Product()
    df_products = get_SOH(df_products_all)
    df_PO_lineItems = get_PO_lineitems(df_po)
    df_incoming = get_incoming(df_PO_lineItems)


    ## Get awaiting stages and then find ETA

    from datetime import timedelta

    dfs_awaiting = dfs[dfs["stage"].isin(['Awaiting Supplier (PO Pending)', 'Awaiting Supplier (Existing PO)','Backorder'])]

    df_awaiting_merged = dfs_awaiting.merge(df_po, how='left', on='match')

    df_awaiting_merged['ETA for customer'] = df_awaiting_merged['PO ETA']+ timedelta(days=3)
    df_awaiting_merged['ETA for customer'] = df_awaiting_merged['ETA for customer'].dt.strftime('%d/%m/%Y')

    df_awaiting_merged = df_awaiting_merged[['reference','firstName','lastName','company','SO ETA','stage','code','name','qty','internalComments','lineComments','qtyShipped','holdingQty','BO Qty','PO Ref_x','PO Stage','PO ETA','ETA for customer']]

    df_awaiting_PO_ETA = df_awaiting_merged.dropna(subset=['PO ETA'])
    df_awaiting_PO_ETA = df_awaiting_PO_ETA[df_awaiting_PO_ETA['stage'].isin(['Awaiting Supplier (PO Pending)', 'Awaiting Supplier (Existing PO)'])]

    df_awaiting_PO_NOETA = df_awaiting_merged[df_awaiting_merged['PO ETA'].isna()]
    #df_awaiting_PO_NOETA['No ETA for'] =date.today() -  df_awaiting_PO_NOETA['createdDate'].dt.date


    df_awaiting_PO_ETA.to_csv('Awaiting Supplier ETA - Already has ETA - '+date.today().strftime("%d-%m-%Y")+'.csv')
    df_awaiting_PO_NOETA.to_csv('Awaiting Supplier ETA and BO - NO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv')



    df_po.to_csv('PO NEW - '+date.today().strftime("%d-%m-%Y")+'.csv')
    df_products.to_csv('SOH - '+date.today().strftime("%d-%m-%Y")+'.csv')

    #check awaiting existing and backorder
    #Find bo item with stock availablity <0 and incoming is not enough to cover

    #get incoming to product

    df_products_incoming = df_products.merge(df_incoming, how='left', on='code')
    df_products_incoming = df_products_incoming.fillna(0)

    dfs_BO_A = dfs[dfs["stage"].isin(['Awaiting Supplier (Existing PO)','Backorder'])]
    dfs_BO_NoPO = dfs_BO_A.merge(df_products_incoming, how='left', on='code')
    dfs_BO_NoPO['Qty to order'] = (dfs_BO_NoPO['stockAvailable'] + dfs_BO_NoPO['incoming']) *-1
    df_BO_To_Order = dfs_BO_NoPO[dfs_BO_NoPO['Qty to order']>0]
    df_BO_To_Order =df_BO_To_Order[(df_BO_To_Order['code']!='miscitem')]

    df_BO_To_Order.to_csv('BO item with not enough incoming to cover - '+date.today().strftime("%d-%m-%Y")+'.csv')


    dfs_BO = dfs[dfs["stage"].isin(['Awaiting Supplier (PO Pending)', 'Awaiting Supplier (Existing PO)','Backorder'])]

    dfs_BO_WS = dfs_BO

    dfs_BO_WS.to_csv('Wholesaler BO Report - '+date.today().strftime("%d-%m-%Y")+'.csv')

    #SO with SO ETA past due

    dfs_BO_SO_DUE = dfs_BO[dfs_BO['SO ETA'].dt.date <date.today()]
    dfs_BO_SO_DUE['Overdue Days'] = date.today() - dfs_BO_SO_DUE['SO ETA'].dt.date
    dfs_BO_SO_DUE['Overdue Days'] = dfs_BO_SO_DUE['Overdue Days'].astype(str).apply(lambda x:x.replace(' days',''))
    dfs_BO_SO_DUE['Overdue Days'] = dfs_BO_SO_DUE['Overdue Days'].astype(float)

    dfs_BO_SO_DUE = dfs_BO_SO_DUE.sort_values(by=['SO ETA'])


    dfs_BO_SO_DUE.to_csv('BO with SO ETA overdue - '+date.today().strftime("%d-%m-%Y")+'.csv')


    dfs_BO_SOH = dfs_BO.merge(df_products, how='left', on='code')
    dfs_BO_SOH =dfs_BO_SOH[(dfs_BO_SOH['SOH']>0)]
    dfs_BO_SOH =dfs_BO_SOH[(dfs_BO_SOH['code']!='miscitem')]

    dfs_BO_SOH.to_csv('BO items with SOH - '+date.today().strftime("%d-%m-%Y")+'.csv')


    #Current overdue
    dfs_BO_overdue = dfs_BO.merge(df_po, how='left', on='match')
    dfs_BO_overdue = dfs_BO_overdue.dropna()

    dfs_BO_overdue = dfs_BO_overdue[dfs_BO_overdue['PO ETA'].dt.date <date.today()]

    dfs_BO_overdue['Overdue Days'] = dfs_BO_overdue['PO ETA'].dt.date - dfs_BO_overdue['SO ETA'].dt.date
    dfs_BO_overdue['Overdue Days'] = dfs_BO_overdue['Overdue Days'].astype(str).apply(lambda x:x.replace(' days',''))
    dfs_BO_overdue['Overdue Days'] = dfs_BO_overdue['Overdue Days'].astype(float)
    dfs_BO_overdue['PO ETA'] = dfs_BO_overdue['PO ETA'].dt.strftime("%d-%m-%Y")

    dfs_BO_overdue = dfs_BO_overdue[['reference','firstName','lastName','company','stage','code','name','qty','internalComments','lineComments','qtyShipped','holdingQty','BO Qty','PO Ref_x','PO Stage','SO ETA','PO ETA','Overdue Days']]
    dfs_BO_overdue = dfs_BO_overdue.sort_values(by=['SO ETA'])

    dfs_BO_overdue.to_csv('BO with overdue PO - '+date.today().strftime("%d-%m-%Y")+'.csv')

    #future overdue - where PO ETA > SO ETA
    dfs_BO_f_overdue = dfs_BO.merge(df_po, how='left', on='match')
    dfs_BO_f_overdue = dfs_BO_f_overdue[dfs_BO_f_overdue['SO ETA'].dt.date <dfs_BO_f_overdue['PO ETA'].dt.date]

    dfs_BO_f_overdue['Overdue Days'] = dfs_BO_f_overdue['PO ETA'].dt.date - dfs_BO_f_overdue['SO ETA'].dt.date
    dfs_BO_f_overdue['Overdue Days'] = dfs_BO_f_overdue['Overdue Days'].astype(str).apply(lambda x:x.replace(' days',''))
    dfs_BO_f_overdue['Overdue Days'] = dfs_BO_f_overdue['Overdue Days'].astype(float)


    dfs_BO_f_overdue['PO ETA'] = dfs_BO_f_overdue['PO ETA'].dt.strftime("%d-%m-%Y")
    dfs_BO_f_overdue['SO ETA'] = dfs_BO_f_overdue['SO ETA'].dt.strftime("%d-%m-%Y")

    dfs_BO_f_overdue = dfs_BO_f_overdue[['reference','firstName','lastName','company','stage','code','name','qty','internalComments','lineComments','qtyShipped','holdingQty','BO Qty','PO Ref_x','PO Stage','SO ETA','PO ETA','Overdue Days']]
    dfs_BO_f_overdue = dfs_BO_f_overdue.sort_values(by=['SO ETA'])

    dfs_BO_f_overdue.to_csv('BO with PO ETA later than SO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv')

    f1 = 'BO with PO ETA later than SO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv' #PO ETA > SO ETA
    f2 = 'BO with overdue PO - '+date.today().strftime("%d-%m-%Y")+'.csv' # PO ETA < Today
    f3 = 'BO items with SOH - '+date.today().strftime("%d-%m-%Y")+'.csv' #BO has stock to cover
    f4 = 'BO item with not enough incoming to cover - '+date.today().strftime("%d-%m-%Y")+'.csv' #BO has not enough incoming to cover
    f5 = 'Awaiting Supplier ETA - Already has ETA - '+date.today().strftime("%d-%m-%Y")+'.csv'
    f6 = 'Awaiting Supplier ETA and BO - NO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv'
    f7 = 'BO with SO ETA overdue - '+date.today().strftime("%d-%m-%Y")+'.csv'

    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = "BO report - "+date.today().strftime("%d-%m-%Y")
    body = "Daily Report Email"
    sender_email = "mail@photogear.co.nz"
    receiver_email = "jeff@photogear.co.nz"
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


    add_file(f1)
    add_file(f2)
    add_file(f3)
    add_file(f4)
    add_file(f5)
    add_file(f6)
    add_file(f7)

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

    import numpy as np
    import pandas as pd
    from pandas import json_normalize 
    import matplotlib.pyplot as plt
    import requests
    import json
    import time as time
    from datetime import date
    from datetime import timedelta


    def get_Product():
        #get Products
        url = "https://api.cin7.com/api/v1/Products"

        page = 1
        new_results = True
        products = []
        #while new_results:
        querystring = {"page":page,"rows":"250","where":"status='Public'","fields":"id, name, productOptions"}

        while new_results:
            querystring = {"page":page,"rows":"250","where":"status='Public'","fields":"id, name, productOptions"}
            headers = {
            'authorization': "Basic UGhvdG9nZWFyMk5aOjU1NTI3YjBmNzJjMDRjNjliNWZiMzI3NDliMWYxYzQy",
            'cache-control': "no-cache",
            'postman-token': "d57962dc-1d76-6652-ec65-3765f5feb6ba"
            }

            r = requests.request("GET", url, headers=headers, params=querystring)
            new_results = r.json()
            products.extend(new_results)
            page += 1
            time.sleep(1/3)

        dfp = pd.DataFrame.from_dict(products)

        return dfp

    def get_SO():
        

        #get Sales Orders
        url = "https://api.cin7.com/api/v1/SalesOrders"

        page = 1
        new_results = True
        orders = []
        #while new_results:
        querystring = {"page":page,"rows":"250","where":"DispatchedDate IS NULL","fields":"id, Stage, Status, LineItems, Reference, FirstName, LastName, Company, EstimatedDeliveryDate, InternalComments, createdDate"}

        while new_results:
            querystring = {"page":page,"rows":"250","where":"DispatchedDate IS NULL","fields":"id, Stage, Status, LineItems, Reference, FirstName, LastName, Company, EstimatedDeliveryDate, InternalComments, createdDate"}
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

        dfs = pd.DataFrame.from_dict(orders)

        #remove void
        dfs = dfs[dfs["status"].isin(['APPROVED'])]
        return dfs


    def get_SO_lineitems (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["lineItems"])

        i = 1
        dfy = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfy = dfy.append(pd.json_normalize(dfx[i]))
            i+=1

        dfs = df.drop(columns=['lineItems'])
        dfs = dfs.merge(dfy, how='left', left_on='id', right_on='transactionId')
        dfs = dfs.drop(columns=['id_x','status','parentId','productId','productOptionId','integrationRef','sort','option1','option3','styleCode','barcode','sizeCodes','unitCost','unitPrice','discount','accountCode','stockControl','stockMovements'])

        dfs = dfs.rename(columns={"option2": "PO Ref", "estimatedDeliveryDate" : "SO ETA"})
        dfs['match'] = dfs['PO Ref'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').replace('\t','').lower())
        dfs['SO ETA'] = pd.to_datetime(dfs['SO ETA'])
        #dfs['createdDate'] = pd.to_datetime(dfs['createdDate'])


        #Taking only items that has BO Qty
        dfs['BO Qty'] = dfs['qty'] - dfs['qtyShipped'] - dfs['holdingQty']
        dfs = dfs[dfs["BO Qty"]>0]

        return dfs

    def get_SOH (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["productOptions"])

        i = 1
        dfz = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfz = dfz.append(pd.json_normalize(dfx[i]))
            i+=1

        dfz = dfz[['id','code','stockOnHand','productId', 'stockAvailable']]
        dfz = dfz.rename(columns={"stockOnHand": "SOH"})
        dfz = df.merge(dfz, how='left', left_on='id', right_on='productId')
        dfz = dfz[['code','name','SOH', 'stockAvailable']]

        return dfz

    def get_PO():
        

        #get Sales Orders
        url = "https://api.cin7.com/api/v1/PurchaseOrders"

        page = 1
        new_results = True
        orders = []
        #while new_results:
        querystring = {"page":page,"rows":"250","where":"FullyReceivedDate IS NULL","fields":"id, Stage, Status, Reference, FirstName, LastName, Company, LineItems, EstimatedArrivalDate"}

        while new_results:
            querystring = {"page":page,"rows":"250","where":"FullyReceivedDate IS NULL","fields":"id, Stage, Status, Reference, FirstName, LastName, Company, LineItems, EstimatedArrivalDate"}
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

        #remove void
        df2 = df2[df2["status"].isin(['APPROVED'])]

        df2 = df2.rename(columns={"reference": "PO Ref","estimatedArrivalDate":"PO ETA","stage":"PO Stage"})
        df2 = df2[['PO Ref','PO Stage','PO ETA','lineItems']]
        df2['match'] = df2['PO Ref'].astype(str).apply(lambda x:x.replace('$','').replace('\r','').replace(' ','').replace('-','').replace('(','').replace(')','').replace('/','').replace('\t','').lower())
        df2['PO ETA'] = pd.to_datetime(df2['PO ETA'])


        return df2

    def get_PO_lineitems (df):
        #expand the lineitems
        dfx = pd.json_normalize(df["lineItems"])

        i = 1
        dfy = pd.json_normalize(dfx[0])

        while i< dfx.shape[1]:
            dfy = dfy.append(pd.json_normalize(dfx[i]))
            i+=1

        dfy = dfy[dfy['qty']>0]

        return dfy

    def get_incoming(df):
        
        df = df[['code','name', 'qty']]
        table = pd.pivot_table(df, values='qty', index=['code'], aggfunc=np.sum)
        table = table.rename(columns={"qty": "incoming"})
        
        return table

    dfs = get_SO()
    dfs = get_SO_lineitems(dfs)
    df_po = get_PO()
    df_products_all = get_Product()
    df_products = get_SOH(df_products_all)
    df_PO_lineItems = get_PO_lineitems(df_po)
    df_incoming = get_incoming(df_PO_lineItems)


    ## Get awaiting stages and then find ETA

    from datetime import timedelta

    dfs_awaiting = dfs[dfs["stage"].isin(['Awaiting Supplier (PO Pending)', 'Awaiting Supplier (Existing PO)','Backorder'])]

    df_awaiting_merged = dfs_awaiting.merge(df_po, how='left', on='match')

    df_awaiting_merged['ETA for customer'] = df_awaiting_merged['PO ETA']+ timedelta(days=3)
    df_awaiting_merged['ETA for customer'] = df_awaiting_merged['ETA for customer'].dt.strftime('%d/%m/%Y')

    df_awaiting_merged = df_awaiting_merged[['reference','firstName','lastName','company','SO ETA','stage','code','name','qty','internalComments','lineComments','qtyShipped','holdingQty','BO Qty','PO Ref_x','PO Stage','PO ETA','ETA for customer']]

    df_awaiting_PO_ETA = df_awaiting_merged.dropna(subset=['PO ETA'])
    df_awaiting_PO_ETA = df_awaiting_PO_ETA[df_awaiting_PO_ETA['stage'].isin(['Awaiting Supplier (PO Pending)', 'Awaiting Supplier (Existing PO)'])]

    df_awaiting_PO_NOETA = df_awaiting_merged[df_awaiting_merged['PO ETA'].isna()]
    #df_awaiting_PO_NOETA['No ETA for'] =date.today() -  df_awaiting_PO_NOETA['createdDate'].dt.date


    df_awaiting_PO_ETA.to_csv('Awaiting Supplier ETA - Already has ETA - '+date.today().strftime("%d-%m-%Y")+'.csv')
    df_awaiting_PO_NOETA.to_csv('Awaiting Supplier ETA and BO - NO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv')



    df_po.to_csv('PO - '+date.today().strftime("%d-%m-%Y")+'.csv')
    df_products.to_csv('SOH - '+date.today().strftime("%d-%m-%Y")+'.csv')

    #check awaiting existing and backorder
    #Find bo item with stock availablity <0 and incoming is not enough to cover

    #get incoming to product

    df_products_incoming = df_products.merge(df_incoming, how='left', on='code')
    df_products_incoming = df_products_incoming.fillna(0)

    dfs_BO_A = dfs[dfs["stage"].isin(['Awaiting Supplier (Existing PO)','Backorder'])]
    dfs_BO_NoPO = dfs_BO_A.merge(df_products_incoming, how='left', on='code')
    dfs_BO_NoPO['Qty to order'] = (dfs_BO_NoPO['stockAvailable'] + dfs_BO_NoPO['incoming']) *-1
    df_BO_To_Order = dfs_BO_NoPO[dfs_BO_NoPO['Qty to order']>0]
    df_BO_To_Order =df_BO_To_Order[(df_BO_To_Order['code']!='miscitem')]

    df_BO_To_Order.to_csv('BO item with not enough incoming to cover - '+date.today().strftime("%d-%m-%Y")+'.csv')


    dfs_BO = dfs[dfs["stage"].isin(['Awaiting Supplier (PO Pending)', 'Awaiting Supplier (Existing PO)','Backorder'])]


    #SO with SO ETA past due

    dfs_BO_SO_DUE = dfs_BO[dfs_BO['SO ETA'].dt.date <date.today()]
    dfs_BO_SO_DUE['Overdue Days'] = date.today() - dfs_BO_SO_DUE['SO ETA'].dt.date
    dfs_BO_SO_DUE = dfs_BO_SO_DUE.sort_values(by=['SO ETA'])


    dfs_BO_SO_DUE.to_csv('BO with SO ETA overdue - '+date.today().strftime("%d-%m-%Y")+'.csv')


    dfs_BO_SOH = dfs_BO.merge(df_products, how='left', on='code')
    dfs_BO_SOH =dfs_BO_SOH[(dfs_BO_SOH['SOH']>0)]
    dfs_BO_SOH =dfs_BO_SOH[(dfs_BO_SOH['code']!='miscitem')]

    dfs_BO_SOH.to_csv('BO items with SOH - '+date.today().strftime("%d-%m-%Y")+'.csv')


    #Current overdue
    dfs_BO_overdue = dfs_BO.merge(df_po, how='left', on='match')
    dfs_BO_overdue = dfs_BO_overdue.dropna()

    dfs_BO_overdue = dfs_BO_overdue[dfs_BO_overdue['PO ETA'].dt.date <date.today()]

    dfs_BO_overdue['PO ETA'] = dfs_BO_overdue['PO ETA'].dt.strftime("%d-%m-%Y")

    dfs_BO_overdue = dfs_BO_overdue[['reference','firstName','lastName','company','stage','code','name','qty','internalComments','lineComments','qtyShipped','holdingQty','BO Qty','PO Ref_x','PO Stage','SO ETA','PO ETA']]
    dfs_BO_overdue = dfs_BO_overdue.sort_values(by=['SO ETA'])

    dfs_BO_overdue.to_csv('BO with overdue PO - '+date.today().strftime("%d-%m-%Y")+'.csv')

    #future overdue - where PO ETA > SO ETA
    dfs_BO_f_overdue = dfs_BO.merge(df_po, how='left', on='match')
    dfs_BO_f_overdue = dfs_BO_f_overdue[dfs_BO_f_overdue['SO ETA'].dt.date <dfs_BO_f_overdue['PO ETA'].dt.date]

    dfs_BO_f_overdue['Overdue Days'] = dfs_BO_f_overdue['PO ETA'].dt.date - dfs_BO_f_overdue['SO ETA'].dt.date

    dfs_BO_f_overdue['PO ETA'] = dfs_BO_f_overdue['PO ETA'].dt.strftime("%d-%m-%Y")
    dfs_BO_f_overdue['SO ETA'] = dfs_BO_f_overdue['SO ETA'].dt.strftime("%d-%m-%Y")

    dfs_BO_f_overdue = dfs_BO_f_overdue[['transactionId','id_y','reference','firstName','lastName','company','stage','code','name','qty','internalComments','lineComments','qtyShipped','holdingQty','BO Qty','PO Ref_x','PO Stage','SO ETA','PO ETA','Overdue Days']]
    dfs_BO_f_overdue = dfs_BO_f_overdue.sort_values(by=['SO ETA'])

    dfs_BO_f_overdue.to_csv('BO with PO ETA later than SO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv')

def email_report(emailadd):
    import email, smtplib, ssl

    from email import encoders
    from email.mime.base import MIMEBase    
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    subject = "BO report - "+date.today().strftime("%d-%m-%Y")
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

    f1 = 'BO with PO ETA later than SO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv' #PO ETA > SO ETA
    f2 = 'BO with overdue PO - '+date.today().strftime("%d-%m-%Y")+'.csv' # PO ETA < Today
    f3 = 'BO items with SOH - '+date.today().strftime("%d-%m-%Y")+'.csv' #BO has stock to cover
    f4 = 'BO item with not enough incoming to cover - '+date.today().strftime("%d-%m-%Y")+'.csv' #BO has not enough incoming to cover
    f5 = 'Awaiting Supplier ETA - Already has ETA - '+date.today().strftime("%d-%m-%Y")+'.csv'
    f6 = 'Awaiting Supplier ETA and BO - NO ETA - '+date.today().strftime("%d-%m-%Y")+'.csv'
    f7 = 'BO with SO ETA overdue - '+date.today().strftime("%d-%m-%Y")+'.csv'
    

    add_file(f1)
    add_file(f2)
    add_file(f3)
    add_file(f4)
    add_file(f5)
    add_file(f6)
    add_file(f7)

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def run():
    get_BO_Report()
    email_report('jay@photogear.co.nz')
    email_report('harry@photogear.co.nz')
    email_report('sales@photogear.co.nz')
    email_report('jeff@photogear.co.nz')
