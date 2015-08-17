#!/usr/bin/env python
# -*- coding: utf-8 -*-

import email
from email.header import decode_header, make_header
import getpass
import imaplib
import re
import MySQLdb as mdb
import sys
import datetime

# ask for inputs
startdate = raw_input("Enter the start date in DD-MMM-YYYY format (i.e. 01-Aug-2015): ")
enddate = raw_input("Enter the end date in DD-MMM-YYYY format (i.e. 01-Aug-2015): ")
text = '流利号'
print text
# searchquery = "(SINCE \"%s\" BEFORE \"%s\")" % (startdate, enddate)
# searchquery = "(SINCE \"%s\")" % (startdate)
# print searchquery

# connect to gmail imap server
mail = imaplib.IMAP4_SSL('imap.gmail.com')
# password = getpass.getpass("Enter your password: ")
mail.login('hunter@liulishuo.com', 'l1i2u3l4i5')
mail.list()

# get the count of support emails
mail.select('Support')
# varEmailcount = int(varEmailcount[1][0])

# date = "05-Aug-2015"
# date2 = "10-Aug-2015"
# typ, data = mail.uid('search', None, '(SINCE {startdate} BEFORE {enddate} TEXT {text})'.format(startdate=startdate, enddate=enddate, text=text))
typ, data = mail.uid('search', None, '(TEXT {text})'.format(text=text))
ids = data[0]
id_list = ids.split()

#get the most recent email id
latest_email_id = int( id_list[-1] )

# create log file
f = open("support_email_log.txt", "w")
f.write("Support emails between %s and %s \n" % (startdate, enddate))

def get_decoded_email_body(message_body):
    """ Decode email body.
    Detect character set if the header is not set.
    We try to get text/plain, but if there is not one then fallback to text/html.
    :param message_body: Raw 7-bit message body input e.g. from imaplib. Double encoded in quoted-printable and latin-1
    :return: Message body as unicode string
    """

    msg = email.message_from_string(message_body)

    text = ""
    if msg.is_multipart():
        html = None
        for part in msg.walk():

            # print "%s, %s" % (part.get_content_type(), part.get_content_charset())

            if part.get_content_charset() is None:
                # We cannot know the character set, so return decoded "something"
                text = part.get_payload(decode=True)
                continue

            charset = part.get_content_charset()

            if part.get_content_type() == 'text/plain':
                text = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if part.get_content_type() == 'text/html':
                html = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            else:
                continue

        if text is not None:
            return text.strip()
        else:
            return html.strip()
    else:
        text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        return text.strip()

# this function looks for the Liulihao in the body of an e-mail
# the Liulihao is 8-10 digits

# are there patterns in Liulihao?

def info_regex(text):
    pattern = '(?!3162034932|1316203493|162034932|62034932)(\d{8,10})'
    results = re.search(pattern, text)
    if results is not None:
        s = results.start()
        e = results.end()
        return text[s:e]
    else:
        return None
    # results = re.findall(pattern, text)
    # if results is not None:
    #     return results
    # else:
    #     return None

# sometimes the message can't be read normally without decoding
# this is for those messages

def info_han_regex(text):
    pattern = '\d{9,10}'
    results = re.findall(pattern, text)
    if results is not None:
        return results
    else:
        # how to insert NULL and not the string "NULL" into MySQL?
        return None

# the message subject will contain the name of the app that the email
# is being sent from
# this converts from Chinese to in-house code names 
   
def subject_regex(text):
    pattern1 = u'口语发音教练'
    pattern2 = u'英语流利说'
    pattern3 = u'流利学院'
    if re.search(pattern1, text):
        return "chipstone"
    elif re.search(pattern2, text):
        return "super"
    elif re.search(pattern3, text):
        return "tydus"
    else:
        return None

# initialize connection to local mysql server
connect  = mdb.connect(host = "localhost",
     port = 3306,
     user = "hunter",
     passwd = "hunter",
     db = "hunter")
# initialize cursor
cursor = connect.cursor()

#iterate through all messages in decending order starting with latest_email_id
#the '-1' dictates reverse looping order

for i in id_list:
    typ, data = mail.uid('fetch', i, '(RFC822)' )
    varBody = ''

    # for each message, we decode the message and take parts we are interested in
    # we want the sender's email, liulihao, app_name, and date
    for response_part in data:
        if isinstance(response_part, tuple):

            # get encoded message and decode
            msg = email.message_from_string(response_part[1])
            print msg
            varBody = get_decoded_email_body(response_part[1])

            # subject will still be encoded so decode into ASCII
            dh = decode_header(msg['subject'])
            default_charset = 'ASCII'

            # use decoded subject to find app name
            varAppName = ''.join([ unicode(t[0], t[1] or default_charset) for t in dh ])
            # print varAppName
            varAppName = subject_regex(varAppName)

            # clean up the sender's email by removing unnecessary characters
            varFrom = msg['from']
            varFrom = varFrom.split(" ")[-1]
            varFrom = varFrom.replace('<', '')
            varFrom = varFrom.replace('>', '')
            # print varFrom

            # convert date to readable MySQL format
            varDate = msg['date']
            varDate = email.utils.parsedate(varDate)
            varDate = datetime.datetime(*(varDate[0:6]))
            varDate = varDate.strftime('%Y-%m-%d %H:%M:%S')

            # get Liulihao
            # varLiulihao = info_regex(varBody)
            varLiulihao = info_regex(varBody)
            # print varLiulihao

            if varLiulihao is not None:
                f.write(varFrom + " | " + varLiulihao + " | Y \n")
            else:
                f.write(varFrom + " | None | N \n")

            # get truncated body if too long
            if len(varBody) > 255:
                varBody = varBody[0:252] + '...'

            # insert information into database
            # database has UNIQUE email key so there are no repetitions
            cursor.execute("""INSERT IGNORE INTO hunter.email_analysis_test (data_date, email, liulihao, app_name, body) 
                VALUES ('%s', '%s', '%s', '%s', '%s')""" % (varDate, varFrom, varLiulihao, varAppName, varBody))
            # cursor.execute("""INSERT IGNORE INTO hunter.email_email_test (email)
            #     VALUES ('%s')""" % (varFrom))

            # cursor.execute("""INSERT IGNORE INTO hunter.email_date_test (data_date)
            #     VALUES ('%s')""" % (varDate))

            # cursor.execute("""REPLACE INTO hunter.email_liulihao_test (liulihao)
            #     VALUES ('%s')""" % (varLiulihao))

            # cursor.execute("""INSERT IGNORE INTO hunter.email_app_name_test (app_name)
            #     VALUES ('%s')""" % (varAppName))
            
            # cursor.execute("""INSERT IGNORE INTO hunter.email_body_test (body)
            #     VALUES ('%s')""" % (varBody))

            # commit the changes
            connect.commit()
# close out the connection to the MySQL database
connect.close()

f.close()

















