#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import xmltodict
import requests
import json
import sendEmail

SMS_LIST_TEMPLATE = '''<request>
    <PageIndex>1</PageIndex>
    <ReadCount>20</ReadCount>
    <BoxType>1</BoxType>
    <SortType>0</SortType>
    <Ascending>0</Ascending>
    <UnreadPreferred>0</UnreadPreferred>
    </request>'''

SMS_DEL_TEMPLATE = '<request><Index>{index}</Index></request>'

"""SMS_SEND_TEMPLATE = '''<request>
    <Index>-1</Index>
    <Phones><Phone>{phone}</Phone></Phones>
    <Sca></Sca>
    <Content>{content}</Content>
    <Length>{length}</Length>
    <Reserved>1</Reserved>
    <Date>{timestamp}</Date>
    </request>'''
    """
    
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def isHilink(device_ip):
    try:
        r = requests.get(url='http://' + device_ip + '/api/device/information', timeout=(2.0,2.0))
    except requests.exceptions.RequestException as e:
        return False;

    if r.status_code != 200:
        return False
    return True
    
def getHeaders(device_ip):
    token = None
    sessionID = None
    try:
        r = requests.get(url='http://' + device_ip + '/api/webserver/SesTokInfo')
    except requests.exceptions.RequestException as e:
        return (token, sessionID)
    try:        
        d = xmltodict.parse(r.text, xml_attribs=True)
        if 'response' in d and 'TokInfo' in d['response']:
            token = d['response']['TokInfo']
        d = xmltodict.parse(r.text, xml_attribs=True)
        if 'response' in d and 'SesInfo' in d['response']:
            sessionID = d['response']['SesInfo']
        headers = {'__RequestVerificationToken': token, 'Cookie': sessionID}
    except:
        pass
    return headers
    

def getSMS(device_ip, headers):
    r = requests.post(url = 'http://' + device_ip + '/api/sms/sms-list', data = SMS_LIST_TEMPLATE, headers = headers)
    d = xmltodict.parse(r.text, xml_attribs=True)
    numMessages = int(d['response']['Count'])
    messagesR = d['response']['Messages']['Message']
    if numMessages == 1:
        temp = messagesR
        messagesR = [temp]
    messages = getContent(messagesR, numMessages)
    return messages, messagesR

def getContent(data, numMessages):
    messages = []
    for i in range(numMessages):
        message = data[i]
        number = message['Phone']
        content = message['Content']
        date = message['Date']
        messages.append('Message from ' + number + ' recieved ' + date + ' : ' + str(content))
    return messages

def delMessage(device_ip, headers, ind):
    r = requests.post(url = 'http://' + device_ip + '/api/sms/delete-sms', data = SMS_DEL_TEMPLATE.format(index=ind), headers = headers)
    d = xmltodict.parse(r.text, xml_attribs=True)
    print(d['response'])

def getUnread(device_ip, headers):
    r = requests.get(url = 'http://' + device_ip + '/api/monitoring/check-notifications', headers = headers)
    d = xmltodict.parse(r.text, xml_attribs=True)
    unread = int(d['response']['UnreadMessage'])
    return unread

if __name__ == "__main__":

    device_ip = '192.168.1.1'
    if not isHilink(device_ip):
        if not isHilink('hi.link'):
            print("Can't find a Huawei HiLink device on the default IP addresses, please try again and pass the device's IP address as a parameter")
            print('')
            sys.exit(-1)
        else:
            device_ip = 'hi.link'
            
    headers = getHeaders(device_ip)
    
    unread = getUnread(device_ip, headers)
    if unread != 0:
    
        messages, messagesR = getSMS(device_ip, headers)

        #Read
        if not os.path.exists(os.path.join(__location__,'data',)):
            os.makedirs(os.path.join(__location__,'data'))
        try:
            f1 = open(os.path.join(__location__,'data',"sms.json"), 'r')
            data = json.load(f1)
            f1.close()
        except:
            data = []
    
        #Append new
        for i in range (len(messages)):
            data.append(messagesR[i])

        #Save
        f2 = open(os.path.join(__location__,'data',"sms.json"), 'w')
        json.dump(data, f2)
        f2.close()

        f3 = open(os.path.join(__location__,'data',"sms.txt"), 'a')
        for i in range (len(messages)):
            f3.write(messages[i] + '\n')
        f3.close()

        #email messages
        for i in range(len(messages)):
            print(messages[i])
            sendEmail.sendmail('SMS ' + messagesR[i]['Date'], messages[i], 'email@email.com')    
     

        #delete from device
        for i in range(len(messagesR)):
            headers = getHeaders(device_ip)
            delMessage(device_ip, headers, messagesR[i]['Index'])

