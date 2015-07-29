import email
import json
import imaplib
import re

# coding: utf8

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('hunter@liulishuo.com', '@D1o2n3g4h1u2n3t4')
mail.list()
mail.select('Support')

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

			print "%s, %s" % (part.get_content_type(), part.get_content_charset())

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

def regexr(text):
  	pattern = '"body":"[0-9]*"'


#iterate through 5 messages in decending order starting with latest_email_id
#the '-1' dictates reverse looping order
for i in range( latest_email_id, latest_email_id-5, -1 ):
   	typ, data = mail.fetch( i, '(RFC822)' )

   	for response_part in data:
	  	if isinstance(response_part, tuple):
			msg = email.message_from_string(response_part[1])
			varSubject = msg['subject']
			varFrom = msg['from']
			print get_decoded_email_body(response_part[1])

	#remove the brackets around the sender email address
	varFrom = varFrom.replace('<', '')
	varFrom = varFrom.replace('>', '')

   #add ellipsis (...) if subject length is greater than 35 characters
   	if len( varSubject ) > 35:
	  	varSubject = varSubject[0:32] + '...'

   	print '[' + varFrom.split()[-1] + '] ' + varSubject