# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from datetime import datetime, date, timedelta
import os, sys
from logging.handlers import TimedRotatingFileHandler

from settings import RULE_DIRS, TIMESTAMP_FMT

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)

today = date.today().strftime(TIMESTAMP_FMT)
yesterday = (date.today() - timedelta(days=1)).strftime(TIMESTAMP_FMT)


def create_dir():
    daily = os.path.join(BASE_DIR, 'daily')
    if not os.path.exists(daily):
        os.mkdir(daily)
    folder = datetime.today().strftime('%Y%m%d')
    dir_path = os.path.join(daily, folder)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    for item in RULE_DIRS:
        sub_dir = os.path.join(dir_path, item)
        if not os.path.exists(sub_dir):
            os.mkdir(sub_dir)
    return dir_path, folder


def push_to_mailbox(msglist, recipients):
    import smtplib
    if sys.version_info.major == 3:
        from email.mime.text import MIMEText
        from email.utils import format_datetime as formatdate
        from email.header import Header
    else:
        from email.MIMEText import MIMEText
        from email.Utils import formatdate
        from email.Header import Header
    smtp_host = 'smtp.sina.cn'
    from_mail = username = 'nuggetstock@sina.com'
    password = 'welcome'
    subject = '[%s] 自动推荐' % datetime.today().strftime('%Y/%m/%d')
    body = '\n'.join(msglist)
    mail = MIMEText(body, 'plain', 'utf-8')
    if sys.version_info.major == 3:
        mail['subject'] = Header(subject, 'utf-8')
        mail['from'] = from_mail
        mail['to'] = recipients
        mail['date'] = formatdate(datetime.now())
    else:
        mail['Subject'] = Header(subject, 'utf-8')
        mail['From'] = from_mail
        mail['To'] = recipients
        mail['Date'] = formatdate()
    try:
        smtp = smtplib.SMTP_SSL(smtp_host)
        smtp.ehlo()
        smtp.login(username, password)
        smtp.sendmail(from_mail, recipients, mail.as_string())
        smtp.close()
    except Exception as e:
        logger.error(str(e))


def is_stock_available(data):
    return today in data or yesterday in data


def set_logger(logger_in, directory, logfile):
    if not os.path.exists(directory):
        os.makedirs(directory)
    log_file_name = os.path.join(directory, logfile)
    log_handler = TimedRotatingFileHandler(log_file_name, when="midnight", encoding='utf8')
    log_handler.suffix = "%Y%m%d_%H%M%S.log"
    log_formatter = logging.Formatter('%(asctime)-12s:%(message)s')
    log_handler.setFormatter(log_formatter)
    stream_handle = logging.StreamHandler()
    stream_handle.setFormatter(log_formatter)
    logger_in.addHandler(log_handler)
    logger_in.addHandler(stream_handle)
    logger_in.setLevel(logging.WARNING)
    return logger_in
