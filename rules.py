# -*- coding=utf-8 -*-

from operator import sub

import numpy as np

from settings import KISS_THRESH1, KISS_THRESH2, KISS_THRESH3
from calculations import calc_diff, detect_zero_points, calc_expma, fast_moving_average


def rule_gold_bar(close_prices, daily_volumes):
    recent_prices = close_prices[-5:]
    recent_volumes = daily_volumes[-5:]
    C1 = recent_prices[4] > recent_prices[3] > recent_prices[2] > recent_prices[1]
    C2 = recent_volumes[4] < recent_volumes[3] < recent_volumes[2] < recent_volumes[1]
    C3 = (recent_prices[1] - recent_prices[0]) / recent_prices[0] > 0.09
    return all([C1, C2, C3])


def rule_gold_cross(ddd, ama, zero_positions):
    dma = ddd - ama
    last_index = ddd.shape[0] - 1
    C1 = dma[last_index] > 0
    if zero_positions.shape[0] < 3:
        C2 = C3 = C4 = C5 = C6 = C7 = C8 = False
    else:
        C2 = np.sum(dma[zero_positions[0]:zero_positions[1]]) > 0
        C3 = np.sum(dma[zero_positions[1]:zero_positions[2]]) <= 0
        C4 = np.sum(dma[zero_positions[0]:zero_positions[2]]) > 0
        C5 = last_index - zero_positions[-1] <= 2
        C6 = ((zero_positions[1] - zero_positions[0]) - 2 * (zero_positions[2] - zero_positions[1])) > 0
        C7 = (zero_positions[2] - zero_positions[1]) < 8
        C8 = ama[zero_positions[2]] - ama[zero_positions[1]] >= 0 or ama[zero_positions[2]] - ama[zero_positions[0]] > 0
    return all([C1, C2, C3, C4, C5, C6, C7, C8])


def rule_gold_kiss(ddd, ama, zero_positions, close_price):
    last_indx = ddd.shape[0] - 1
    dma = ddd - ama
    diff = calc_diff(dma)
    ama_diff = calc_diff(ama)
    diff_zero_positions = detect_zero_points(diff)
    dma_after_zero = dma[zero_positions:]
    max_dma, max_dma_position = np.max(dma_after_zero), np.argmax(dma_after_zero)
    C1 = 0 < dma[last_indx] < KISS_THRESH1 * close_price[last_indx]  # Last day dma Less than Close_price*1.5%
    C2 = 0 < dma[diff_zero_positions[-1]] < KISS_THRESH2 * close_price[
        diff_zero_positions[-1]]  # Kiss day dma Less than Close_price*10%
    C3 = max_dma > KISS_THRESH3 * close_price[zero_positions + max_dma_position]
    C4 = 5 <= (last_indx - zero_positions) <= 120 and (last_indx - diff_zero_positions[
        -1]) <= 2  # Last dma Cross day within 9 weeks, Kiss day within 1 week
    C5 = diff[zero_positions] > 0
    C6 = diff[last_indx] >= 0
    C7 = ama_diff[last_indx] > 0 or ama[diff_zero_positions[-1]] - ama[zero_positions] > 0
    C8 = sum(dma[zero_positions:]) > 0
    return all([C1, C2, C3, C4, C5, C6, C7, C8])


def rule_gold_twine(ddd, ama, close_price):
    dma = ddd - ama
    recent = dma[-16:]
    threshold = 0.01
    return all([abs(item) < threshold * price for item, price in zip(recent, close_price)])


def rule_exp_ma(sequence, last_position):
    EXP1 = calc_expma(sequence, 10)
    EXP2 = calc_expma(sequence, 50)
    DIFEXP = map(sub, EXP1, EXP2)
    EXPZeros = detect_zero_points(DIFEXP)
    C1 = DIFEXP[last_position] > 0
    C2 = (last_position - EXPZeros[-1]) < 5
    return all([C1, C2])


def rule_multi_average(close_price):
    MA5 = fast_moving_average(close_price, 5)
    MA13 = fast_moving_average(close_price, 13)
    MA21 = fast_moving_average(close_price, 21)
    MA34 = fast_moving_average(close_price, 34)
    MA55 = fast_moving_average(close_price, 55)
    C1 = MA5[-1] > MA13[-1] > MA21[-1] > MA34[-1] > MA55[-1]
    C2 = MA5[-2] > MA13[-2] > MA21[-2] > MA34[-2] > MA55[-2]
    C3 = MA5[-3] > MA13[-3] > MA21[-3] > MA34[-3] > MA55[-3]
    return all([C1, not C2, not C3])
