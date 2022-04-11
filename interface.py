import numpy as np
import os
import time
import pandas as pd
from thz_pulse import pulse
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt


class TopticaSocket:
    def __init__(self):
        pass

    def read(self):
        t = np.linspace(-4, 4, 10000)
        p = pulse(t)

        SAMPLE_RATE = len(t) / (t[-1] - t[0]) * 1e12
        N = len(p)
        a = rfft(p)
        f = rfftfreq(N, 1 / SAMPLE_RATE)
        return t, p, f / 1e12, np.abs(a)


if __name__ == "__main__":
    socket = TopticaSocket()
    t, p, f, a = socket.read()
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.plot(t, p)
    ax2.plot(f, a)
    ax2.set_xlim(0,10)
    plt.show()
