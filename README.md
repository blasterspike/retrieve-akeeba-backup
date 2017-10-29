# retrieve-akeeba-backup

#### Table of Contents

1. [Description](#description)
2. [Usage](#usage)
3. [The ini file](#the-ini-file)  
  3.1. [The structure](#the-structure)  
  3.2. [Example](#example)
4. [Retention](#retention)  
  4.1. [Short term](#short-term)  
  4.2. [Long term](#long-term)
5. [Limitations](#limitations)

## Description

This is a script to:  
- trigger an Akeeba Backup in Joomla  
- download locally the file generated using SSH or FTP  
- store the file based on a retention  

At the end of the process, the script will send an e-mail with the total time.  
The script reads all the configurations from an ini file and is intended to be run every day.

## Usage

The script has some dependencies specified in _requirements.txt_, to install them

```bash
pip install -r requirements.txt
```

Provide the full path to the script so it will automatically read the config file from the same directory.  
This script works on Python 3.

```bash
python3 /usr/local/bin/retrieve_akeeba_backup.py
```

## The configuration file

The configuration file is a YAML file, it must be called *config.yml* and it must be placed in the same directory 
where the script is.

### The structure

If you select to use _ssh_, you have to omit the _ftp_ section and vice versa.  
Example of a configuration file with SSH:

```yaml
settings:
  remote_backup_path: <Path on the FTP server to the backup folder of Akeeba Backup>
  trigger_url: <The URL that you need to visit in order to start the backup with Akeeba Backup.
               You can find this string going in backend of Joomla to Components > Akeeba Backup
               > Scheduling Information > Url you want to execute>
  short_term_retention:  <Number of days that you want to keep the backup>
  long_term_retention: <Number of weeks that you want to keep the backup.
                       Only the Sunday backup will be considered to be stored>
  short_term_path: <Path to your daily backups. Integer.>
  long_term_path: <Path to your weekly backups. Integer.>
  domain: <Domain name of your website> 
 
ssh:
  server: <SSH server>
  username: <SSH username>
  port: <SSH port. Integer.>
  pkey_file: <Path to private key>
 
e-mail:
  sender: <e-mail address of the sender>
  receiver: <e-mail address of the receiver>
  smtp_server: <SMTP server name>
```

While if you want to use FTP, delete the SSH key and add instead

```yaml
ftp:
  ftp_server: <FTP server>
  username: <FTP username>
  password: <FTP password>
```

## Retention

### Short term

On the short term retention, files will be kept only for the specified days.  
Example: if you run the script every day and you have set the short_term_retention to 7, all the files in the short_term_path older than 7 days will be deleted.

### Long term

On the long term retention, files will be kept only for the specified weeks.  
Only the backup taken on Sunday will be considered.  
Example: if you run the script every day and you have set the long_term_retention to 26, all the files in the long_term_path older than 26 weeks will be deleted.