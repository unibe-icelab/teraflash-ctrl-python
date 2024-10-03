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


def zero_padding(time, pulse, df_padded=0.01):
    # Calculate the total time span of the original data
    T = time[-1] - time[0]

    # Determine the required number of points to achieve the desired frequency resolution
    N_padded = int(np.ceil(T / df_padded))

    # Find the length of the original signal
    N_original = len(pulse)

    # Calculate the original time step (assuming uniform sampling in the time array)
    dt = time[1] - time[0]

    # If padding is needed, apply zero-padding and extend the time array
    if N_padded > N_original:
        # Pad the pulse array with zeros to match the required length
        padded_pulse = np.pad(pulse, (0, N_padded - N_original), mode='constant')

        # Create an extended time array with the same timestep (dt)
        extended_time = np.arange(time[0], time[0] + N_padded * dt, dt)
    else:
        # If no padding is needed, return the original arrays
        padded_pulse = pulse
        extended_time = time

    return extended_time, padded_pulse


def unwrap_phase(phase):
    threshold = np.pi
    N = len(phase)

    for i in range(N - 1):
        if phase[i + 1] - phase[i] > threshold:
            for j in range(i + 1, N):
                phase[j] -= 2 * np.pi
        elif phase[i + 1] - phase[i] < -threshold:
            for j in range(i + 1, N):
                phase[j] += 2 * np.pi
    return phase


def get_fft(t, p, df=0.01, window_start=1, window_end=7, return_td=False):
    t = np.array(t)
    p = np.array(p) * toptica_window(t, window_start, window_end)
    t, p = zero_padding(t, p, df_padded=df)

    sample_rate = 1 / (t[1] - t[0]) * 1e12
    n = len(p)
    fft = rfft(p)
    a = np.abs(fft)
    angle = np.angle(fft)
    arg = np.unwrap(angle)
    f = rfftfreq(n, 1 / sample_rate) / 1e12
    a = a[f >= 0.1]
    arg = arg[f >= 0.1]
    f = f[f >= 0.1]
    if return_td:
        return t,p,f, a, np.abs(arg)
    else:
        return f, a, np.abs(arg)


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
