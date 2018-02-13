# -*- coding=utf-8 -*-
import logging
import multiprocessing
import os
import time
import traceback
from datetime import datetime, timedelta
from operator import itemgetter

import numpy as np

from calculations import detect_zero_points, calc_dma
from grabber import grab_hfq_price
from helper import push_to_mailbox, set_logger, is_stock_available
from namelist import mails
from rules import rule_gold_cross, rule_gold_kiss, rule_gold_twine, rule_multi_average
from settings import TIMESTAMP_FMT, INTERVAL, RULE_DIRS
from stocks import StockInfo


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
stock_info = StockInfo()
log_file = 'StockBot_%s.log' % datetime.now().strftime('%Y%m%d_%H%M')
log_dir = os.path.join(BASE_DIR, "logs")

logger = logging.getLogger('stock_bot')
logger = set_logger(logger, log_dir, log_file)


def transform(data):
    if not data:
        return np.array([])

    today = datetime.today()
    cnt = 0
    prices = []
    day = 0
    while cnt < min(INTERVAL, len(data.keys())):
        if not is_stock_available(data):
            # 停牌
            break
        current = datetime.strftime(today - timedelta(days=day), TIMESTAMP_FMT)
        close_price = data.get(current)
        if close_price:
            cnt += 1
            prices.append(float(close_price))
        day += 1
    return np.array(prices[::-1])


def gold_seeker(stock_code, index):
    golds_stocks = ()
    try:
        # Get stock name
        stock_name = stock_info.get_stock_name(stock_code)

        # Fetch daily close price
        data = grab_hfq_price(stock_code)

        # Transformation on data
        hfq_close = transform(data)
        if len(hfq_close):
            [ddd, ama, dma] = calc_dma(hfq_close)
            zero_position = detect_zero_points(dma)
            if zero_position.shape[0] < 3:
                logger.warning(
                    'Newstock(<89d) %4s:%4s:%s' % (index, stock_name + (4 - len(stock_name)) * '  ', stock_code))
                return ()

            cross = rule_gold_cross(ddd, ama, zero_position[-3:])
            kiss = rule_gold_kiss(ddd, ama, zero_position[-1], hfq_close)
            twine = rule_gold_twine(ddd, ama, hfq_close)
            multi_range = rule_multi_average(hfq_close)
            category = ['']
            for i, item in enumerate([cross, kiss, twine, multi_range]):
                if item:
                    rule_name = RULE_DIRS[i]
                    gold_info = '{0:8}- {1} {2}({3})'.format(rule_name[4:], stock_code, stock_name.encode('utf-8'),
                                                             stock_info.get_stock_industry(stock_code).encode('utf-8'))
                    category.append(rule_name[4:])
                    golds_stocks = (gold_info, ama[-1])
            logger.warning(
                'Complete%6s:%4s:%s %s' % (index, stock_name + (4 - len(stock_name)) * '  ',
                                           stock_code, '@'.join(category)))
        else:
            # Check if stock is on suspension.
            logger.warning('Suspension%4s:%4s:%s' % (index, stock_name + (4 - len(stock_name)) * '  ', stock_code))
            return ()
    except Exception as e:
        logger.error('Error: %s when processing %s..' % (e, stock_code))  #
        print(traceback.format_exc())

    return golds_stocks


def sort_by_ama(tuple_result):
    ordered_result = sorted(tuple_result, key=itemgetter(1))
    reordered_result = map(itemgetter(0), ordered_result)
    ordered_result = sorted(reordered_result, key=lambda x: x[0:4])
    return ordered_result


def push_notifier(gold_stocks, push_targets):
    if gold_stocks:
        for target in push_targets:
            if target['type'] == 'A':
                candidates = gold_stocks
            elif target['type'] == 'D':
                candidates = [item for item in gold_stocks if item[0] == 'D']
            elif target['type'] == 'm':
                candidates = [item for item in gold_stocks if item[1] == 'm']
            else:
                candidates = [':( Sorry. Keep you money in your pocket safely. No stocks to push today.']
            push_to_mailbox(candidates, target['mail'])
            time.sleep(2)


def multi_process_analyze(stock_list):
    result = []
    pool = multiprocessing.Pool(processes=4)
    for index, stock in enumerate(stock_list):
        result.append(pool.apply_async(gold_seeker, (stock, index,)))
    pool.close()
    pool.join()
    return [res.get() for res in result if res.get()]


if __name__ == '__main__':
    stocks = stock_info.get_stocks()
    results = multi_process_analyze(stocks)
    resort_results = sort_by_ama(results)
    push_notifier(resort_results, mails)