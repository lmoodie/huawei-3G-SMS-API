import smtplib  

def sendmail(subject, message, to):  
    fromaddr = 'EMAIL-ADDRESS'  
    toaddrs  = to  
    msg = "Subject: %s\n\n%s" % (subject, message)
    username = 'EMAIL-ADDRESS'  
    password = 'PASSWORD'  
    server = smtplib.SMTP('smtp.gmail.com:587') #default server for gmail, change if not using gmail
    server.ehlo()
    server.starttls()  
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)  
    server.quit()
