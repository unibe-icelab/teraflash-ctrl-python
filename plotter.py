import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import threading
import os
import time
import serial
import pandas as pd
from interface import TopticaSocket
from matplotlib.widgets import Slider, Button


class MyDataClass():

    def __init__(self):
        self.pulse_time = []
        self.pulse_db = []
        self.freq = []
        self.freq_amp = []


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
        self.h2Line, = self.ax2.plot(0, 0, label="frequencies", color="red")
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
        self.h1Line.set_data(self._dataClass.pulse_time, self._dataClass.pulse_db)
        self.h2Line.set_data(self._dataClass.freq, self._dataClass.freq_amp)

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
        self.socket = TopticaSocket()
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
data = MyDataClass()
plotter = MyPlotClass(data, callback)
fetcher = MyDataFetchClass(data)
try:
    fetcher.start()
    plt.show()
    fetcher.running = False
finally:
    fetcher.join()
    exit()
