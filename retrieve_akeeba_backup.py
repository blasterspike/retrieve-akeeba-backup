#!/usr/bin/python
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# Version: 1.0
# Author: Massimo Vannucci

import ftplib
import logging
import ConfigParser
import requests
import os
import time
import smtplib
from email.mime.text import MIMEText

def send_mail(text, sender, receiver, domain, smtp_server):
    msg = MIMEText(text)
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = 'Backup of ' + domain + ' completed'

    s = smtplib.SMTP(smtp_server)
    s.sendmail(sender, receiver, msg.as_string())
    s.quit()


def rotation(filename, short_term_retention, long_term_retention, short_term_path, long_term_path):
    for file in os.listdir(short_term_path):
        # Get the list of files older than 7 days
        if os.stat(os.path.join(short_term_path, file)).st_mtime < time.time() - int(short_term_retention) * 86400:
            os.remove(os.path.join(short_term_path, file))
            logging.info('Removed ' + file)

    # Every Sunday I keep a copy stored for 6 months
    if time.strftime('%w', time.gmtime()) == 0:
        for file in os.listdir(long_term_path):
            # Like the previous command but multiplied by 26 weeks
            if os.stat(os.path.join(long_term_path, file)).st_mtime < time.time() - int(long_term_retention) * 7 * 86400:
                os.remove(os.path.join(long_term_path, file))
                logging.info('Removed ' + file)
        os.system('cp ' + filename + ' ' + long_term_path)
        logging.info(filename + ' stored in ' + long_term_path)

    os.system('mv ' + filename + ' ' + short_term_path)
    logging.info(filename + ' stored in ' + short_term_path)


def retrieve_from_ftp(ftp_server, username, password, remote_backup_path, domain):
    ftps = ftplib.FTP_TLS(ftp_server)
    ftps.auth()
    ftps.prot_p()
    ftps.login(username, password)
    logging.info('Logged into FTP')
    ftps.cwd(remote_backup_path)

    filename = ftps.nlst('site-' + domain + '-*')[0]
    logging.info('Downloading file ' + filename)

    with open(filename, 'wb') as f:
        ftps.retrbinary('RETR ' + filename, f.write)
    logging.info(filename + ' downloaded')

    # Remove file in web space
    ftps.delete(filename)

    return filename


def main():

    start_time = time.time()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s')

    # Read settings from ini file
    settings = ConfigParser.RawConfigParser(allow_no_value=True)
    ini_file = os.path.dirname(os.path.realpath(__file__)) + '/settings.ini'
    settings.read(ini_file)
    # Set the variables
    ftp_server = settings.get('credentials', 'ftp_server')
    username = settings.get('credentials', 'username')
    password = settings.get('credentials', 'password')
    remote_backup_path = settings.get('settings', 'remote_backup_path')
    trigger_url = settings.get('settings', 'trigger_url')
    short_term_retention = settings.get('settings', 'short_term_retention')
    long_term_retention = settings.get('settings', 'long_term_retention')
    short_term_path = settings.get('settings', 'short_term_path')
    long_term_path = settings.get('settings', 'long_term_path')
    sender = settings.get('e-mail', 'sender')
    receiver = settings.get('e-mail', 'receiver')
    domain = settings.get('e-mail', 'domain')
    smtp_server = settings.get('e-mail', 'smtp_server')

    logging.info('Hitting the URL to call Akeeba Backup')
    session = requests.session()
    session.max_redirects = 10000
    session.get(trigger_url)
    logging.info('Backup created')

    filename = retrieve_from_ftp(ftp_server,
                                 username,
                                 password,
                                 remote_backup_path,
                                 domain)
    rotation(filename,
             short_term_retention,
             long_term_retention,
             short_term_path,
             long_term_path)

    end_time = time.time()
    diff_time = end_time - start_time
    total_time = time.strftime('%H:%M:%S' , time.gmtime(diff_time))

    text = filename + ' backed up in ' + total_time
    send_mail(text, sender, receiver, domain, smtp_server)

    logging.info('Backup procedure completed')


if __name__ == "__main__":
    main()
