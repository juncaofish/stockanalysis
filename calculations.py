# -*- coding=utf-8 -*-

import numpy as np


def detect_zero_points(sequence):
    cross = np.roll(sequence, -1) * sequence
    indices = (cross < 0).nonzero()[0]
    return indices


def fast_moving_average(x, N):
    return np.convolve(x, np.ones((N,)) / N, 'full')[:1 - N]


def calc_expma(sequence, period):
    length = len(sequence)

    def ExpMA(inner_sequence, n, N):
        return inner_sequence[0] if n == 0 else \
            (inner_sequence[n] * 2.0 + (N - 1.0) * ExpMA(inner_sequence, n - 1, N)) / (N + 1.0)

    expma = [ExpMA(sequence, i, period) for i in xrange(length)]
    return expma


def find_close(sequence):
    eps = 0.02
    np_list = np.array(sequence)
    indices = list((abs(np_list) < eps).nonzero()[0])
    return indices


def calc_diff(np_sequence):
    return np.hstack(([1], np.diff(np_sequence))) * 5


def calc_cusum(sequence):
    return [sum(sequence[0:i + 1]) for i, elem in enumerate(sequence)]


def calc_dma(close_prices, short=5, far=89, middle=34):
    ddd = fast_moving_average(close_prices, short) - fast_moving_average(close_prices, far)
    ama = fast_moving_average(ddd, middle)
    dma = ddd - ama
    return ddd, ama, dma


def calc_boll(Close, N=89, k=2):
    """
    # Bollinger Bands consist of:
    # an N-period moving average (MA)
    # an upper band at K times an N-period standard deviation above the moving average (MA + Kσ)
    # a lower band at K times an N-period standard deviation below the moving average (MA − Kσ)
    # %b = (last − lowerBB) / (upperBB − lowerBB)
    # Bandwidth tells how wide the Bollinger Bands are on a normalized basis. Writing the same symbols as before, and middleBB for the moving average, or middle Bollinger Band:
    # Bandwidth = (upperBB − lowerBB) / middleBB
    :param Close:
    :param N:
    :param k:
    :return:
    """

    length = len(Close)
    MA = fast_moving_average(Close, N).tolist()
    # MA = calc_expma(Close, N)
    SM = map(lambda x, y: (x - y) ** 2, Close, MA)
    MD = [(sum(SM[i - N + 1:i + 1] if i >= N - 1 else (SM[0:i] + [SM[i]] * (N - i))) / float(N)) ** 0.5 for i in
          xrange(length)]
    UP = map(lambda x, y: x + y * k, MA, MD)
    DN = map(lambda x, y: x - y * k, MA, MD)
    b = map(lambda x, y, z: (x - z) / (float(y - z) if y != z else 1.0), Close, UP, DN)
    Band = map(lambda x, y, z: (x - z) / (float(y) if y != 0 else 1.0), UP, MD, DN)
    return MA, UP, DN, b, Band
