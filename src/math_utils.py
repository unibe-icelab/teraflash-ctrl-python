import numpy as np
from numpy.fft import rfft, rfftfreq


def blackman_func(n, M):
    return 0.42 - 0.5 * np.cos(2 * np.pi * n / M) + 0.08 * np.cos(4 * np.pi * n / M)


def toptica_window(t, start=1, end=7):
    window = np.ones(t.shape)
    a = t[t <= (t[0] + start)]
    b = t[t >= (t[-1] - end)]
    a = blackman_func(a - a[0], 2 * (a[-1] - a[0]))
    b = blackman_func(b + b[-1] - b[0] - b[0], 2 * (b[-1] - b[0]))
    window[t <= (t[0] + start)] = a
    window[t >= (t[-1] - end)] = b
    return window


def zero_padding(t, p, do_padding=True):
    dt = round(t[1] - t[0], 2)
    df = 1 / (dt * len(t))
    df_padded = 0.01
    pd = int(1 / (dt * df_padded))

    if pd > len(t) and do_padding:
        padding_length = (pd - len(t))
        padding = np.array([0.0] * padding_length)
        dt = t[1] - t[0]
        t = np.append(np.arange(t[0] - dt * padding_length, t[0], dt), t)
        p = np.append(p, padding)
    return t, p


def get_fft(t, p, padding=True, window_start=1, window_end=7):
    t = np.array(t)
    p = np.array(p) * toptica_window(t, window_start, window_end)
    t, p = zero_padding(t, p, padding)

    sample_rate = len(t) / (t[-1] - t[0]) * 1e12
    n = len(p)
    a = np.abs(rfft(p))
    arg = np.unwrap(np.angle(rfft(p)))
    f = rfftfreq(n, 1 / sample_rate) / 1e12
    return f, a, arg
