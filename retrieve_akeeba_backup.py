#!/usr/bin/python
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# Version: 1.0
# Author: Massimo Vannucci

import argparse
import platform
import paramiko
import sys
import ftplib
import logging
import ConfigParser
import requests
import os
import time
import smtplib
from email.mime.text import MIMEText
import re

if platform.system() == 'Darwin':
    import keyring


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
            logging.info('Removed {0}'.format(file))

    # Every Sunday I keep a copy stored for 6 months
    if time.strftime('%w', time.gmtime()) == 0:
        for file in os.listdir(long_term_path):
            # Like the previous command but multiplied by 26 weeks
            if os.stat(os.path.join(long_term_path, file)).st_mtime < time.time() - int(long_term_retention) * 7 * 86400:
                os.remove(os.path.join(long_term_path, file))
                logging.info('Removed {0}'.format(file))
        os.system('cp ' + filename + ' ' + long_term_path)
        logging.info('{0} stored in {1}'.format(filename, long_term_path))

    os.system('mv ' + filename + ' ' + short_term_path)
    logging.info('{0} stored in {1}'.format(filename, short_term_path))


def retrieve_from_ftp(ftp_server, username, password, remote_backup_path, domain):
    ftps = ftplib.FTP_TLS(ftp_server)
    ftps.auth()
    ftps.prot_p()
    ftps.login(username, password)
    logging.info('Logged into FTP')
    ftps.cwd(remote_backup_path)

    filename = ftps.nlst('site-' + domain + '-*')[0]
    logging.info('Downloading file {0}'.format(filename))

    with open(filename, 'wb') as f:
        ftps.retrbinary('RETR ' + filename, f.write)
    logging.info('{0} downloaded'.format(filename))

    # Remove file in web space
    ftps.delete(filename)
    logging.info('Deleted {0} on the server'.format(filename))

    return filename


def retrieve_from_ssh(ssh_server, username, port, pkey_file, remote_backup_path, domain):
    if platform.system() == 'Darwin':
        password = keyring.get_password('SSH', pkey_file)
        key = paramiko.RSAKey.from_private_key_file(pkey_file, password=password)
    elif platform.system() == 'Linux':
        key = paramiko.RSAKey.from_private_key_file(pkey_file)
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    # To avoid the error
    # paramiko.ssh_exception.SSHException: Server '$server' not found in known_hosts
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ssh_server, username=username, port=port, pkey=key)
    logging.info('Connected using SSH')
    sftp = ssh.open_sftp()
    # http://docs.paramiko.org/en/1.17/api/sftp.html#paramiko.sftp_client.SFTPClient

    files = sftp.listdir(remote_backup_path)
    logging.debug('List of files: {0}'.format(files))
    for file in files:
        match = re.match(r'site-' + domain + '-.*', file)
        # This is to avoid match = None
        if match:
            filename = match.group(0)
    logging.info('Downloading file {0}'.format(filename))
    sftp.get(remote_backup_path + filename, filename)
    logging.info('{0} downloaded'.format(filename))

    # Remove file in web space
    sftp.remove(remote_backup_path + filename)
    logging.info('Deleted {0} on the server'.format(filename))

    sftp.close()
    ssh.close()

    return filename


def main():

    start_time = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', '-m', help='Select the mode to connect to the server: FTP or SSH', required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s')

    # Read settings from ini file
    settings = ConfigParser.RawConfigParser(allow_no_value=True)
    ini_file = os.path.dirname(__file__) + '/settings.ini'
    logging.debug('ini file path: {0}'.format(ini_file))
    settings.read(ini_file)
    # Set the variables
    if args.mode == 'ftp':
        ftp_server = settings.get('ftp', 'ftp_server')
        username = settings.get('ftp', 'username')
        password = settings.get('ftp', 'password')
    elif args.mode == 'ssh':
        ssh_server = settings.get('ssh', 'ssh_server')
        username = settings.get('ssh', 'username')
        port = int(settings.get('ssh', 'port'))
        pkey_file = settings.get('ssh', 'pkey_file')
    else:
        logging.error('No valid mode provided. Specify either ftp or ssh.')
        sys.exit(1)
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

    if args.mode == 'ftp':
        filename = retrieve_from_ftp(ftp_server,
                                     username,
                                     password,
                                     remote_backup_path,
                                     domain)
    elif args.mode == 'ssh':
        filename = retrieve_from_ssh(ssh_server,
                                     username,
                                     port,
                                     pkey_file,
                                     remote_backup_path,
                                     domain)
    else:
        logging.error('No valid mode provided. Specify either ftp or ssh.')
        sys.exit(1)

    rotation(filename,
             short_term_retention,
             long_term_retention,
             short_term_path,
             long_term_path)

    end_time = time.time()
    diff_time = end_time - start_time
    total_time = time.strftime('%H:%M:%S', time.gmtime(diff_time))

    text = filename + ' backed up in ' + total_time
    send_mail(text, sender, receiver, domain, smtp_server)

    logging.info('Backup procedure completed')


if __name__ == "__main__":
    main()
