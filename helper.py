# -*- coding=utf-8 -*-
import logging
from datetime import datetime, date, timedelta
import os
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


def push_to_mailbox(_msglist, _sendto):
    import smtplib
    from email.MIMEText import MIMEText
    from email.Utils import formatdate
    from email.Header import Header
    smtpHost = 'smtp.sina.cn'
    fromMail = username = 'nuggetstock@sina.com'
    password = 'welcome'
    subject = u'[%s] 自动推荐' % datetime.today().strftime('%Y/%m/%d')
    body = '\n'.join(_msglist)
    mail = MIMEText(body, 'plain', 'utf-8')
    mail['Subject'] = Header(subject, 'utf-8')
    mail['From'] = fromMail
    mail['To'] = _sendto
    mail['Date'] = formatdate()
    try:
        smtp = smtplib.SMTP_SSL(smtpHost)
        smtp.ehlo()
        smtp.login(username, password)
        smtp.sendmail(fromMail, _sendto, mail.as_string())
        smtp.close()
    except Exception as e:
        print(str(e))


def is_stock_available(data):
    return today in data or yesterday in data


def set_logger(logger_in, directory, logfile):
    if not os.path.exists(directory):
        os.makedirs(directory)
    log_file_name = os.path.join(directory, logfile)
    log_handler = TimedRotatingFileHandler(log_file_name, when="midnight")
    log_handler.suffix = "%Y%m%d_%H%M%S.log"
    log_formatter = logging.Formatter('%(asctime)-12s:%(message)s')
    log_handler.setFormatter(log_formatter)
    stream_handle = logging.StreamHandler()
    stream_handle.setFormatter(log_formatter)
    logger_in.addHandler(log_handler)
    logger_in.addHandler(stream_handle)
    logger_in.setLevel(logging.WARNING)
    return logger_in
