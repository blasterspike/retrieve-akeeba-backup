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
- download locally the file generated using FTP  
- store the file based on a retention  

At the end of the process, the script will send an e-mail with the total time.  
The script reads all the configurations from an ini file and is intended to be run every day.

## Usage

Provide the full path to the script so it will automatically read the ini file from the same directory.

```bash
python /usr/local/bin/retrieve_akeeba_backup.py
```

If you want to redirect the output

```bash
python /usr/local/bin/retrieve_akeeba_backup.py >> /usr/local/bin/retrieve_akeeba_backup.log 2>&1
```

## The ini file

The ini file must be called *settings.ini* and must be place in the same directory where the script is.  
All the fields are mandatory.

### The structure

```ini
[credentials]
ftp_server = <FTP server>
username = <FTP username>
password = <FTP password>

[settings]
remote_backup_path = <Path on the FTP server to the backup folder of Akeeba Backup>
trigger_url = <The URL that you need to visit in order to start the backup with Akeeba Backup.
               You can find this string going in backend of Joomla to Components > Akeeba Backup
               > Scheduling Information > Url you want to execute>
short_term_retention =  <Number of days that you want to keep the backup>
long_term_retention = <Number of weeks that you want to keep the backup.
                       Only the Sunday backup will be considered to be stored>
short_term_path = <Where you want to store your daily backups>
long_term_path = <Where you want to store your weekly backups>

[e-mail]
sender = <e-mail address of the sender>
receiver = <e-mail address of the receiver>
domain = <Domain name of your website. Used in the e-mail notification>
smtp_server = <SMTP server name>
```

### Example

```ini
[credentials]
ftp_server = ftp.domain.com
username = jtitor
password = REYuweqATr35#uc

[settings]
remote_backup_path = /administrator/components/com_akeeba/backup/
trigger_url = https://website.com/index.php?option=com_akeeba&view=backup&key=fe6aWr2cubrapr5mamuf
short_term_retention = 7
long_term_retention = 26
short_term_path = /volume1/Backup/Automatic/website/Daily/
long_term_path = /volume1/Backup/Automatic/website/Long term/

[e-mail]
sender = example_email@gmail.com
receiver = example_email@gmail.com
domain = website.com
smtp_server = localhost
```

## Retention

### Short term

On the short term retention, files will be kept only for the specified days.  
Example: if you run the script every day and you have set the short_term_retention to 7, all the files in the short_term_path older than 7 days will be deleted.

### Long term

On the long term retention, files will be kept only for the specified weeks.  
Only the backup taken on Sunday will be considered.  
Example: if you run the script every day and you have set the long_term_retention to 26, all the files in the long_term_path older than 26 weeks will be deleted.

## Limitations

This script has been tested on:  
OS: Synolody DSM 5.2-5644  
Python: 2.7.9
