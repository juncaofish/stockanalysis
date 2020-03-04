# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import sys
from datetime import datetime, date, timedelta
from logging.handlers import TimedRotatingFileHandler

from settings import RULE_DIRS, TIMESTAMP_FMT

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('stock_bot')
today = date.today().strftime(TIMESTAMP_FMT)
yesterday = (date.today() - timedelta(days=1)).strftime(TIMESTAMP_FMT)
color = ['red', 'MediumSeaGreen']


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


def generate_subject():
    return '[%s] 自动推荐' % datetime.today().strftime('%Y/%m/%d')


def generate_header():
    try:
        from grabber import dapan
        sh = dapan('sh000001')
        sz = dapan('sz399001')
        sh_header = '<font color="{color}" size="3">{header}</font>'.format(
            color=color[1 - (sh['percent'] > 0)],
            header='上证指数：{:.2%} （{}）'.format(
                sh['percent'], sh['close']
            ))
        sz_header = '<font color="{color}" size="3">{header}</font>'.format(
            color=color[1 - (sz['percent'] > 0)],
            header='深证指数：{:.2%} （{}）'.format(
                sz['percent'], sz['close']
            ))
        template = '<h2>{}</h2><h2>{}</h2><br>' \
                   '<hr style="height:1px;border:none;border-top:1px dashed #0066CC;" />'
        return template.format(sh_header, sz_header)
    except Exception:
        return '<hr style="height:1px;border:none;border-top:1px dashed #0066CC;" />'


def generate_body(push_items):
    lines = [generate_header()]
    items_cnt = len(push_items)
    if items_cnt > 0:
        push_items = push_items[:15]
        template = '<font face="arial" color="black" size="5"><b>{code}</b></font>' \
                   '<font size="4" color="{color}"> - {name}</font>' \
                   '<font color="gray" size="3"> - ({field})</font>' \
                   '<font color="gray" size="2"> - {rule}</font>'
        for item in push_items:
            item['color'] = color[1 - item['positive']]
            lines.append(template.format(**item))
        if items_cnt > 15:
            lines.append('<font color="gray" size="2">...</font>')
    else:
        body = '<font color="#424242" size="4">' \
               ':( Keep money in your pocket safely. No stocks to recommend today.' \
               '</font>'
        lines.append(body)
    return '<br>'.join(lines)


def push_to_mailbox(push_items, recipients):
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

    subject = generate_subject()
    body = generate_body(push_items)

    mail = MIMEText(body, 'html', 'utf-8')

    if sys.version_info.major == 3:
        mail['subject'] = Header(subject, 'utf-8')
        mail['from'] = from_mail
        mail['to'] = recipients
        mail['date'] = formatdate(datetime.now())
    else:
        mail['Subject'] = Header(subject, 'utf-8')
        mail['From'] = from_mail
        mail['To'] = recipients
        mail['Date'] = formatdate(datetime.now())
    try:
        smtp = smtplib.SMTP_SSL(smtp_host)
        smtp.ehlo()
        smtp.login(username, password)
        smtp.sendmail(from_mail, recipients, mail.as_string())
        smtp.close()
        return True
    except Exception as e:
        logger.error(str(e))
        return False


def stock_alive(data):
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
    logger_in.setLevel(logging.INFO)
    return logger_in
