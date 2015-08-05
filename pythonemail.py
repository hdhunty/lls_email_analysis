# -*- coding: utf-8 -*-

import email
from email.header import decode_header, make_header
import imaplib
import re
import MySQLdb as mdb
import sys
import datetime

# connect to gmail imap server
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('hunter@liulishuo.com', 'l1i2u3l4i5')
mail.list()

# get the count of support emails
varEmailcount = mail.select('Support')
varEmailcount = int(varEmailcount[1][0])

typ, data = mail.search(None, 'ALL')
ids = data[0]
id_list = ids.split()

#get the most recent email id
latest_email_id = int( id_list[-1] )

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

        if text is not None:
            return text.strip()
        else:
            return html.strip()
    else:
        text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        return text.strip()

# this function looks for the Liulihao in the body of an e-mail
# the Liulihao is 8-10 digits
def info_regex(text):
    pattern = '\d{8,10}'
    results = re.search(pattern, text)
    if results is not None:
        s = results.start()
        e = results.end()
        return text[s:e]
    else:
        return "NULL"

# sometimes the message can't be read normally without decoding
# this is for those messages
def info_han_regex(text):
    pattern = '\d{9,10}'
    results = re.findall(pattern, text)
    if results is not None:
        return results
    else:
        return "NULL"

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
        return "NULL"

# initialize connection to local mysql server
connect  = mdb.connect(host = "localhost",
     port = 3306,
     user = "hunter",
     passwd = "hunter",
     db = "hunter")
# initialize server
cursor = connect.cursor()

#iterate through all messages in decending order starting with latest_email_id
#the '-1' dictates reverse looping order
for i in range(latest_email_id, latest_email_id-varEmailcount, -1):
    typ, data = mail.fetch( i, '(RFC822)' )

    # for each message, we decode the message and take parts we are interested in
    # we want the sender's email, liulihao, app_name, and date
    for response_part in data:
        if isinstance(response_part, tuple):
            # get encoded message and decode
            msg = email.message_from_string(response_part[1])
            body = get_decoded_email_body(response_part[1])

            # subject will still be encoded so decode into ASCII
            dh = decode_header(msg['subject'])
            default_charset = 'ASCII'

            # use decoded subject to find app name
            varAppName = ''.join([ unicode(t[0], t[1] or default_charset) for t in dh ])
            varAppName = subject_regex(varAppName)

            # clean up the sender's email by removing unnecessary characters
            varFrom = msg['from']
            varFrom = varFrom.split(" ")[-1]
            varFrom = varFrom.replace('<', '')
            varFrom = varFrom.replace('>', '')

            # convert date to readable MySQL format
            varDate = msg['date']
            varDate = email.utils.parsedate(varDate)
            varDate = datetime.datetime(*(varDate[0:6]))
            varDate = varDate.strftime('%Y-%m-%d %H:%M:%S')

            # get Liulihao
            varLiulihao = info_regex(body)

            # insert information into database
            # database has UNIQUE email key so there are no repetitions
            cursor.execute("""REPLACE INTO hunter.email_analysis (data_date, email, liulihao, app_name) 
                VALUES ('%s', '%s', '%s', '%s')""" % (varDate, varFrom, varLiulihao, varAppName))

            # commit the changes
            connect.commit()
# close out the connection to the MySQL database
connect.close()



















