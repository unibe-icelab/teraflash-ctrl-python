import numpy as np
from numpy.fft import rfft, rfftfreq, irfft


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
        # Extend the time axis
        t = np.linspace(t[0], t[-1] + padding_length * dt, len(t) + padding_length)
        p = np.append(p, padding)
    return t, p


def get_fft(t, p, padding=True, window_start=1, window_end=7):
    t = np.array(t)
    p = np.array(p) * toptica_window(t, window_start, window_end)
    t, p = zero_padding(t, p, padding)

    sample_rate = len(t) / (t[-1] - t[0]) * 1e12
    n = len(p)
    fft = rfft(p)
    a = np.abs(fft)
    angle = np.angle(fft)
    arg = np.unwrap(angle)
    f = rfftfreq(n, 1 / sample_rate) / 1e12
    return f, a, arg


def get_ifft(frequencies, amplitudes, phases, t0=0):
    fft = amplitudes * np.exp(1j * phases)
    signal = irfft(fft)
    delta_f = frequencies[1] - frequencies[0]
    sample_rate = 2 * (len(frequencies) - 1) * delta_f
    N = len(signal)  # Number of samples
    T = 1.0 / sample_rate  # Sample spacing (inverse of the sampling rate)
    time = np.linspace(0.0, N * T, N, endpoint=False)
    return time + t0, signal


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    t = np.arange(1935, 1965.05, 0.05, )
    p = np.ones(t.shape)
    print(f"{t=}")
    print(f"{p=}")

    plt.plot(t, p)
    t_padded, p_padded = zero_padding(t, p)
    p_windowed = p * toptica_window(t)
    t_windowed, p_windowed = zero_padding(t, p_windowed)
    plt.plot(t_windowed, p_windowed)
    plt.show()
