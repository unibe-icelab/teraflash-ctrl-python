import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import threading
from interface import TopticaDataSocket, TopticaConfigSocket
from matplotlib.widgets import Slider, Button
from dummy_client import TCPclient
import logging
import time


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


if __name__ == "__main__":

    logging.basicConfig(filename='logs/main.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.getLogger('matplotlib.font_manager').disabled = True
    logging.getLogger('matplotlib.ticker').disabled = True

    debug = True

    if debug:
        logging.debug("entered debug mode")
        dummy_client = TCPclient()
        dummy_conf = threading.Thread(target=dummy_client.run_config)
        dummy_stream = threading.Thread(target=dummy_client.run_stream)
    else:
        logging.info("entered normal mode")

    callback = CallbackClass()
    dataclass = MyDataClass()
    plotter = MyPlotClass(dataclass, callback)

    dat = TopticaDataSocket(dataclass, debug)
    conf = TopticaConfigSocket(dataclass, debug)

    fetcher = threading.Thread(target=dat.read)
    setter = threading.Thread(target=conf.run)

    try:
        fetcher.start()
        setter.start()
        if debug:
            time.sleep(1)
            dummy_conf.start()
            dummy_stream.start()
        plt.show()

        dat.running = False
        conf.running = False
        if debug:
            dummy_client.running = False

    finally:
        fetcher.join()
        setter.join()
        if debug:
            dummy_conf.join()
            dummy_stream.join()
        exit()
