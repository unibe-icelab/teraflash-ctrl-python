import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import threading
import os
import time
import serial
import pandas as pd
from interface import TopticaDataSocket, TopticaConfigSocket
from matplotlib.widgets import Slider, Button


class MyDataClass():

    def __init__(self):
        self.time = np.zeros(1000)
        self.signal_1 = np.zeros(1000)
        self.freq_1 = np.zeros(1000)
        self.freq_1_amp = np.zeros(1000)
        self.ref_1 = np.zeros(1000)
        self.signal_2 = np.zeros(1000)
        self.ref_2 = np.zeros(1000)


class CallbackClass():
    def __init__(self):
        self.i = 0

    def nxt(self):
        self.i += 1
        print(self.i)

    def prev(self):
        self.i -= 1
        print(self.i)

    def update(self, val):
        self.i = val


class MyPlotClass():

    def __init__(self, dataClass, cb):
        self._dataClass = dataClass
        self.cb = cb
        plt.style.use('dark_background')
        fig, (self.ax1, self.ax2) = plt.subplots(2, 1)

        self.h1Line, = self.ax1.plot(0, 0, label="pulse", color="red")
        self.h2Line, = self.ax2.semilogy(0, 0, label="frequencies", color="red")
        self.ax1.set_xlabel("time [ps]")
        self.ax1.set_ylabel("amplitude [db]")
        self.ax2.set_xlabel("frequency [THz]")
        self.ax2.set_ylabel("amplitude [a.u.]")
        # bnext = Button(self.ax3, 'Next')
        # bnext.on_clicked(self.cb.nxt())
        slider_ax = fig.add_axes([0.13, 0, 0.3, 0.02])

        self.freq_slider = Slider(
            ax=slider_ax,
            label='Frequency [Hz]',
            valmin=0.1,
            valmax=30,
            valinit=0,
        )
        self.ani = FuncAnimation(plt.gcf(), self.run, interval=1, repeat=True)

    def run(self, i):
        if len(self._dataClass.time) == len(self._dataClass.signal_1):
            self.h1Line.set_data(self._dataClass.time, self._dataClass.signal_1)
            self.h2Line.set_data(self._dataClass.freq_1, self._dataClass.freq_1_amp)

        self.ax1.relim()
        self.ax2.relim()
        # freq = 0.05
        # self.h1Line.axes.set_xlim(max(self._dataClass.tData[-1] - 50 * freq, 0),
        #                           self._dataClass.tData[-1] + 10 * freq)
        self.ax2.set_xlim(0, 10)

        self.ax1.autoscale_view()
        self.ax2.autoscale_view()


class MyDataFetchClass(threading.Thread):

    def __init__(self, dataClass):
        threading.Thread.__init__(self)

        # initialize serial port
        self.socket = TopticaDataSocket()
        self._dataClass = dataClass
        self.running = True

    def run(self):
        while self.running:
            # Aquire and parse data from spectrometer
            t, p, f, a = self.socket.read()
            self._dataClass.pulse_time = t
            self._dataClass.pulse_db = p
            self._dataClass.freq = f
            self._dataClass.freq_amp = a
            time.sleep(0.1)


callback = CallbackClass()
dataclass = MyDataClass()
plotter = MyPlotClass(dataclass, callback)
# fetcher = MyDataFetchClass(data)

dat = TopticaDataSocket(dataclass)
conf = TopticaConfigSocket(dataclass)

fetcher = threading.Thread(target=dat.read)
setter = threading.Thread(target=conf.run)

try:
    fetcher.start()
    setter.start()
    plt.show()
    # fetcher.running = False
finally:
    fetcher.join()
    setter.join()
    exit()
