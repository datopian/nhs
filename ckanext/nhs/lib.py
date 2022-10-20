# encoding: utf-8
import smtplib
import socket
import ckan
import logging
from ckan.plugins import toolkit as tk
from time import time
from email.mime.text import MIMEText
from email.header import Header
from email import Utils
from paste.deploy import converters

from ckan.common import _

class MailerException(Exception):
    pass

log = logging.getLogger(__name__)

def mail_html(recipient_name, recipient_email,
                    sender_name, sender_url, subject,
                    body, headers=None):

    if not headers:
        headers = {}

    mail_from = tk.config.get('smtp.mail_from')
    msg = MIMEText(body.encode('utf-8'), 'html', 'utf-8')
    for k, v in headers.items():
        if k in msg.keys():
            msg.replace_header(k, v)
        else:
            msg.add_header(k, v)
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _("%s <%s>") % (sender_name, mail_from)
    recipient = u"%s <%s>" % (recipient_name, recipient_email)
    msg['To'] = Header(recipient, 'utf-8')
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__

    # Send the email using Python's smtplib.
    smtp_connection = smtplib.SMTP()
    if 'smtp.test_server' in tk.config:
        # If 'smtp.test_server' is configured we assume we're running tests,
        # and don't use the smtp.server, starttls, user, password etc. options.
        smtp_server = tk.config['smtp.test_server']
        smtp_starttls = False
        smtp_user = None
        smtp_password = None
    else:
        smtp_server = tk.config.get('smtp.server', 'localhost')
        smtp_starttls = converters.asbool(
            tk.config.get('smtp.starttls'))
        smtp_user = tk.config.get('smtp.user')
        smtp_password = tk.config.get('smtp.password')

    try:
        smtp_connection.connect(smtp_server)
    except socket.error as e:
        log.exception(e)
        raise MailerException('SMTP server could not be connected to: "%s" %s'
                              % (smtp_server, e))
    try:
        # Identify ourselves and prompt the server for supported features.
        smtp_connection.ehlo()

        # If 'smtp.starttls' is on in CKAN config, try to put the SMTP
        # connection into TLS mode.
        if smtp_starttls:
            if smtp_connection.has_extn('STARTTLS'):
                smtp_connection.starttls()
                # Re-identify ourselves over TLS connection.
                smtp_connection.ehlo()
            else:
                raise MailerException("SMTP server does not support STARTTLS")

        # If 'smtp.user' is in CKAN tk.config, try to login to SMTP server.
        if smtp_user:
            assert smtp_password, ("If smtp.user is configured then "
                                   "smtp.password must be config ured as well.")
            smtp_connection.login(smtp_user, smtp_password)

        smtp_connection.sendmail(mail_from, [recipient_email], msg.as_string())
        log.info("Sent email to {0}".format(recipient_email))

    except smtplib.SMTPException as e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)
    finally:
        smtp_connection.quit()
