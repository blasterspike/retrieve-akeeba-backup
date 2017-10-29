#!/usr/bin/python
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# Version: 2.0
# Author: Massimo Vannucci

import platform
import paramiko
import sys
import ftplib
import logging
import yaml
import requests
import os
import time
import smtplib
from email.mime.text import MIMEText
import re

if platform.system() == 'Darwin':
    import keyring


def check_configuration(logger, config_data):
    if all(x in ['ssh', 'ftp'] for x in config_data.keys()):
        logger.error('You can\'t declare both SSH and FTP configuration')
        sys.exit(1)

    if not any(x in ['ssh', 'ftp'] for x in config_data.keys()):
        logger.error('You need to specify either an SSH or an FTP configuration')
        sys.exit(1)

    if 'settings' not in config_data.keys():
        logger.error('You need to specify settings key')
    else:
        if 'remote_backup_path' not in config_data['settings'].keys():
            logger.error('You need to specify remote_backup_path key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['remote_backup_path'], str):
                logger.error('remote_backup_path in settings must be a string')
                sys.exit(1)

        if 'trigger_url' not in config_data['settings'].keys():
            logger.error('You need to specify trigger_url key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['trigger_url'], str):
                logger.error('trigger_url in settings must be a string')
                sys.exit(1)

        if 'short_term_retention' not in config_data['settings'].keys():
            logger.error('You need to specify short_term_retention key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['short_term_retention'], int):
                logger.error('short_term_retention in settings must be an integer')
                sys.exit(1)

        if 'long_term_retention' not in config_data['settings'].keys():
            logger.error('You need to specify long_term_retention key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['long_term_retention'], int):
                logger.error('long_term_retention in settings must be an integer')
                sys.exit(1)

        if 'short_term_path' not in config_data['settings'].keys():
            logger.error('You need to specify short_term_path key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['short_term_path'], str):
                logger.error('short_term_path in settings must be a string')
                sys.exit(1)

        if 'long_term_path' not in config_data['settings'].keys():
            logger.error('You need to specify long_term_path key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['long_term_path'], str):
                logger.error('long_term_path in settings must be a string')
                sys.exit(1)

        if 'domain' not in config_data['settings'].keys():
            logger.error('You need to specify domain key in settings')
            sys.exit(1)
        else:
            if not isinstance(config_data['settings']['domain'], str):
                logger.error('domain in settings must be a string')
                sys.exit(1)

    if 'e-mail' not in config_data.keys():
        logger.error('You need to specify e-mail key')
    else:
        if 'sender' not in config_data['e-mail'].keys():
            logger.error('You need to specify sender key in e-mail')
            sys.exit(1)
        else:
            if not isinstance(config_data['e-mail']['sender'], str):
                logger.error('sender in e-mail must be a string')

        if 'receiver' not in config_data['e-mail'].keys():
            logger.error('You need to specify receiver key in e-mail')
            sys.exit(1)
        else:
            if not isinstance(config_data['e-mail']['receiver'], str):
                logger.error('receiver in e-mail must be a string')

        if 'smtp_server' not in config_data['e-mail'].keys():
            logger.error('You need to specify smtp_server key in e-mail')
            sys.exit(1)
        else:
            if not isinstance(config_data['e-mail']['smtp_server'], str):
                logger.error('smtp_server in e-mail must be a string')

    for x in config_data.keys():
        if x == 'ssh':
            if 'server' not in config_data['ssh'].keys():
                logger.error('You need to specify server key in ssh')
                sys.exit(1)
            else:
                if not isinstance(config_data['ssh']['server'], str):
                    logger.error('server in ssh must be a string')

            if 'username' not in config_data['ssh'].keys():
                logger.error('You need to specify username key in ssh')
                sys.exit(1)
            else:
                if not isinstance(config_data['ssh']['username'], str):
                    logger.error('username in ssh must be a string')

            if 'port' not in config_data['ssh'].keys():
                logger.error('You need to specify port key in ssh')
                sys.exit(1)
            else:
                if not isinstance(config_data['ssh']['port'], int):
                    logger.error('port in ssh must be an integer')

            if 'pkey_file' not in config_data['ssh'].keys():
                logger.error('You need to specify pkey_file key in ssh')
                sys.exit(1)
            else:
                if not isinstance(config_data['ssh']['pkey_file'], str):
                    logger.error('pkey_file in ssh must be a string')

            return 'ssh'
        elif x == 'ftp':
            if 'server' not in config_data['ftp'].keys():
                logger.error('You need to specify server key in ftp')
                sys.exit(1)
            else:
                if not isinstance(config_data['ftp']['server'], str):
                    logger.error('server in ftp must be a string')

            if 'username' not in config_data['ftp'].keys():
                logger.error('You need to specify username key in ftp')
                sys.exit(1)
            else:
                if not isinstance(config_data['ftp']['username'], str):
                    logger.error('username in ftp must be a string')

            if 'password' not in config_data['ftp'].keys():
                logger.error('You need to specify password key in ftp')
                sys.exit(1)
            else:
                if not isinstance(config_data['ftp']['password'], str):
                    logger.error('password in ftp must be a string')

            return 'ftp'


def send_mail(text, sender, receiver, domain, smtp_server):
    msg = MIMEText(text)
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = 'Backup of ' + domain + ' completed'

    s = smtplib.SMTP(smtp_server)
    s.sendmail(sender, receiver, msg.as_string())
    s.quit()


def rotation(logger, filename, short_term_retention, long_term_retention, short_term_path, long_term_path):
    for file in os.listdir(short_term_path):
        # Get the list of files older than 7 days
        if os.stat(os.path.join(short_term_path, file)).st_mtime < time.time() - int(short_term_retention) * 86400:
            os.remove(os.path.join(short_term_path, file))
            logger.info('Removed {0}'.format(file))

    # Every Sunday I keep a copy stored for a period specified by long_term_retention in settings.ini
    if time.strftime('%w', time.gmtime()) == '0':
        for file in os.listdir(long_term_path):
            if os.stat(os.path.join(long_term_path, file)).st_mtime < time.time() - int(long_term_retention) * 7 * 86400:
                os.remove(os.path.join(long_term_path, file))
                logger.info('Removed {0}'.format(file))
        os.system('cp ' + filename + ' "' + long_term_path + '"')
        logger.info('{0} stored in {1}'.format(filename, long_term_path))

    os.system('mv ' + filename + ' "' + short_term_path + '"')
    logger.info('{0} stored in {1}'.format(filename, short_term_path))


def retrieve_from_ftp(logger, ftp_server, username, password, remote_backup_path, domain):
    ftps = ftplib.FTP_TLS(ftp_server)
    ftps.auth()
    ftps.prot_p()
    ftps.login(username, password)
    logger.info('Logged into FTP')
    ftps.cwd(remote_backup_path)

    filename = ftps.nlst('site-' + domain + '-*')[0]
    logger.info('Downloading file {0}'.format(filename))

    with open(filename, 'wb') as f:
        ftps.retrbinary('RETR ' + filename, f.write)
    logger.info('{0} downloaded'.format(filename))

    # Remove file in web space
    ftps.delete(filename)
    logger.info('Deleted {0} on the server'.format(filename))

    return filename


def retrieve_from_ssh(logger, ssh_server, username, port, pkey_file, remote_backup_path, domain):
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
    logger.info('Connected using SSH')
    sftp = ssh.open_sftp()
    # http://docs.paramiko.org/en/1.17/api/sftp.html#paramiko.sftp_client.SFTPClient

    files = sftp.listdir(remote_backup_path)
    logger.debug('List of files: {0}'.format(files))
    for file in files:
        match = re.match(r'site-' + domain + '-.*', file)
        # This is to avoid match = None
        if match:
            filename = match.group(0)
    logger.info('Downloading file {0}'.format(filename))
    sftp.get(remote_backup_path + filename, filename)
    logger.info('{0} downloaded'.format(filename))

    # Remove file in web space
    sftp.remove(remote_backup_path + filename)
    logger.info('Deleted {0} on the server'.format(filename))

    sftp.close()
    ssh.close()

    return filename


def main():

    start_time = time.time()

    logger = logging.getLogger('retrieve_akeeba_backup_logging')
    logger.setLevel(logging.INFO)
    # Create file handler
    fh = logging.FileHandler('retrieve_akeeba_backup.log')
    # Create console handler
    ch = logging.StreamHandler()
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # Add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    with open('config.yml', 'r') as config_file:
        try:
            config_data = yaml.load(config_file)
        except yaml.YAMLError as exc:
            print('Unable to read configuration file: {0}'.format(exc))
            sys.exit(1)

    mode = check_configuration(logger, config_data)

    logger.info('Hitting the URL to call Akeeba Backup')
    session = requests.session()
    session.max_redirects = 10000
    session.get(config_data['settings']['trigger_url'])
    logger.info('Backup created')

    if mode == 'ftp':
        filename = retrieve_from_ftp(logger,
                                     config_data['ftp']['server'],
                                     config_data['ftp']['username'],
                                     config_data['ftp']['password'],
                                     config_data['settings']['remote_backup_path'],
                                     config_data['settings']['domain'])
    elif mode == 'ssh':
        filename = retrieve_from_ssh(logger,
                                     config_data['ssh']['server'],
                                     config_data['ssh']['username'],
                                     config_data['ssh']['port'],
                                     config_data['ssh']['pkey_file'],
                                     config_data['settings']['remote_backup_path'],
                                     config_data['settings']['domain'])

    rotation(logger,
             filename,
             config_data['settings']['short_term_retention'],
             config_data['settings']['long_term_retention'],
             config_data['settings']['short_term_path'],
             config_data['settings']['long_term_path'])

    end_time = time.time()
    diff_time = end_time - start_time
    total_time = time.strftime('%H:%M:%S', time.gmtime(diff_time))

    text = filename + ' backed up in ' + total_time
    send_mail(text,
              config_data['e-mail']['sender'],
              config_data['e-mail']['receiver'],
              config_data['settings']['domain'],
              config_data['e-mail']['smtp_server'])

    logger.info('Backup procedure completed')


if __name__ == "__main__":
    main()
