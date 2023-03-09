def get_onhold():    
    import numpy as np
    import pandas as pd
    from pandas import json_normalize 
    import matplotlib.pyplot as plt
    import requests
    import json
    import time as time
    from datetime import date

    #get Sales Orders
    url = "https://api.cin7.com/api/v1/SalesOrders"

    page = 1
    new_results = True
    orders = []
    #while new_results:
    querystring = {"page":page,"rows":"250","where":"DispatchedDate IS NULL","fields":"id, BranchId, DistributionBranchId, LineItems, Reference, FirstName, LastName, Company"}

    while new_results:
        querystring = {"page":page,"rows":"250","where":"DispatchedDate IS NULL","fields":"id, BranchId, DistributionBranchId, LineItems, Reference, FirstName, LastName, Company"}
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


    #if no distribution branch then set distribution branch = branch
    n = dfs['distributionBranchId'] == 0
    dfs['distributionBranchId'] = np.where((n),dfs['branchId'],dfs['distributionBranchId'])
    branches = pd.read_csv('Branches.csv')

    dfs = pd.merge(dfs, 
                        branches, 
                        left_on ='distributionBranchId', 
                        right_on = 'id',
                        how ='left',
                        )
    dfsa = dfs.drop(columns=['branchId','distributionBranchId','id_y'])

    dfx = pd.json_normalize(dfs["lineItems"])

    i = 1
    dfy = pd.json_normalize(dfx[0])

    while i< dfx.shape[1]:
        dfy = dfy.append(pd.json_normalize(dfx[i]))
        i+=1


    dfy = dfy[dfy['holdingQty']>0]
    dfy = dfy[['transactionId','code','name','lineComments','holdingQty']]
    dfy.rename(columns={'name': 'item name'}, inplace=True)

    onhold = pd.merge(dfy, 
                        dfsa, 
                        left_on ='transactionId', 
                        right_on = 'id_x',
                        how ='left',
                        )

    onhold.rename(columns={'company_y': 'branchName', 'firstName_x':'firstName','lastName_x':'lastName','company_x':'company'}, inplace=True)
    onhold_1 = onhold[['branchName','reference','firstName','lastName','company','code','item name','holdingQty','lineComments']]
    onhold_1.sort_values(by=['branchName','reference','firstName'], inplace=True)

    onhold_1.to_csv('onhold - '+date.today().strftime("%d-%m-%Y")+'.csv')
    f1 = 'onhold - '+date.today().strftime("%d-%m-%Y")+'.csv'

    import email, smtplib, ssl
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    def send_mail(email):
        subject = "On Hold report - "+date.today().strftime("%d-%m-%Y")
        body = "On Hold Report Email"
        sender_email = "mail@photogear.co.nz"
        receiver_email = email
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

        text = message.as_string()

        # Log in to server using secure context and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("mx1.sitehost.co.nz", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)



    send_mail('arneth@photogear.co.nz')
    send_mail('jay@photogear.co.nz')
    send_mail('luke@photogear.co.nz')
    send_mail('zhengwei@photogear.co.nz')
    send_mail('martin@photogear.co.nz')
    send_mail('jeff@photogear.co.nz')

def run():
    get_onhold()

run()