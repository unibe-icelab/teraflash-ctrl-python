import logging
import queue
import threading
import time
from typing import Optional
import re

import numpy as np
import os

from interface import TopticaSocket
import interface
from pulse_detection import detect_pulse


class TeraFlash:

    def __init__(self,
                 ip: str = "169.254.84.101",
                 rng: int = 50,
                 t_begin: float = 1000.0,
                 antenna_range: float = 1000.0,
                 avg: int = 2,
                 log_file=None):
        """
            TeraFlash object used to handle all top level interactions with the user
        Args:
            ip: ip-address of the device (instrument)
            rng: initial range in ps
            t_begin: initial start time of the window in ps
            avg: initial number of measurements to average
            log_file: name of the logfile, if required
        """
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00\x00'
        self.send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
        self.r_stat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00'

        if log_file:
            if not os.path.isdir("logs"):
                os.mkdir("logs")
            if not log_file.endswith(".log"):
                log_file += ".log"
            if os.path.exists(f"logs/{log_file}"):
                log_file = f"{int(time.time())}" + log_file
            logging.basicConfig(filename=f"logs/{log_file}", level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler())

        self.laser = False
        self.emitter = [False, False]
        self.acquisition = False
        self.allowed_antenna_ranges = [antenna_range]
        self.antenna_range = antenna_range
        self.range = rng
        self.t_begin = t_begin
        self.avg = avg

        self.ip = ip

        self.cmd_queue = queue.Queue()
        self.running = threading.Event()
        self.connected = threading.Event()
        self.cmd_ack = threading.Event()
        self.buffer_emptied = threading.Event()
        self.range_changed = threading.Event()
        self.acq_running = threading.Event()
        self.avg_data = threading.Event()
        self.cmd_ack.clear()
        self.connected.clear()
        self.running.set()
        self.buffer_emptied.set()
        self.range_changed.clear()
        self.acq_running.clear()
        self.avg_data.clear()

        try:
            self.socket = TopticaSocket(self.ip, self.running, self.connected, self.cmd_ack, self.buffer_emptied,
                                        self.range_changed, self.acq_running, self.avg_data)
        except ConnectionError:
            logging.error("[INIT] Device is not connected. Check cabling")
            exit()

        # configure tcp config socket
        self.config_thread = threading.Thread(target=self.socket.run_conf_tcp, args=(self.cmd_queue,))

        # configure tcp data socket
        self.data_thread = threading.Thread(target=self.socket.run_tcp_dat, args=(self.cmd_queue,))

        # launch threads
        self.data_thread.start()
        self.config_thread.start()

        # wait until a device is connected
        self.connected.wait()

        # start setup sequence
        self.setup()

        # wait some time to gather data
        time.sleep(3)

    def __enter__(self):
        """
            Entry point of the context manager
        Returns: self

        """
        return self

    def __exit__(self, tp, value, traceback):
        """
            Exit point of the context manager, closes the TCP connection properly
        Args:
            tp: -
            value: -
            traceback: -
        """
        # disconnect routine
        self.disconnect()
        time.sleep(1)
        self.running.clear()
        # if a device was connected, wait for the TCP threads to finish
        if self.connected.is_set():
            self.data_thread.join()
            self.config_thread.join()
        logging.debug("[EXIT] disconnected from device")

    @staticmethod
    def reset_tcp_avg():
        # reset global variable avg
        shape = interface.data.signal_1.shape
        interface.data.signal_1 = np.zeros(shape)
        interface.data.signal_2 = np.zeros(shape)
        interface.n_avg = 0

    @staticmethod
    def get_n_avg():
        # return global variable
        return interface.n_avg

    @staticmethod
    def get_data():
        # return global variable
        return interface.data

    @staticmethod
    def get_status():
        # return global variable
        return interface.status

    def setup(self):
        """
            performs the setup sequence of the device as reconstructed
            by using wireshark on the official application
        """

        logging.info("[INIT] setting up the device...")
        self.get_sys_status()
        self.get_sys_status()

        # wait for status to be available
        while self.get_status() is None:
            time.sleep(1)

        self.allowed_antenna_ranges = self.extract_tia_sens(self.get_status())
        self.set_channel()
        self.set_mode()
        self.set_transmission()
        self.set_antenna_range(self.antenna_range)
        self.set_acq_begin(self.t_begin)
        self.set_acq_avg()
        self.set_acq_stop()
        self.set_acq_range(self.range)
        self.get_sys_monitor()
        self.set_acq_avg(self.avg)
        self.set_acq_range(self.range)
        self.get_sys_monitor()
        self.get_sys_status()
        self.range_changed.clear()
        logging.info("[INIT] device is ready.")

    def disconnect(self):
        """
            disconnects from the device, order of calls is important!
        """
        logging.debug("[CMD] disconnecting from device")
        self.set_acq_stop()
        self.set_emitter(1, False)
        self.set_emitter(2, False)
        self.set_laser(False)

    def get_sys_status(self):
        """
            request the system status string
        """
        logging.debug("[CMD] requesting status")
        cmd = (b'\x14', "SYSTEM : TELL STATUS")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def extract_tia_sens(self, text: str) -> Optional[list[float]]:
        """
        Extracts TIA-Sens(nA) values from the given string.
        Returns a list of floats, or None if not found.
        """
        print(text)
        match = re.search(r"TIA-Sens\(nA\):\s*([0-9.,\s]+)", text)
        if not match:
            return None

        values_str = match.group(1)
        # Split by comma, trim, and convert to floats
        values = [float(v.strip()) for v in values_str.split(",") if v.strip()]
        print(values)
        logging.debug(f"[CMD] supported ranges: {values}")

        return values

    def get_sys_monitor(self):
        """
            this is repeatedly called in the official application
        """
        cmd = (b'\x12', "SYSTEM : MONITOR 1")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def set_channel(self, channel: str = "D"):
        """
            sets dual or single channel mode
        Args:
            channel: The desired mode
        """
        logging.debug(f"[CMD] setting channel: {channel}")
        cmd = (b'\x0b', f"CHANNEL : {channel}")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def set_mode(self, motion: str = "NORMAL"):
        """
            sets the motion mode
        Args:
            motion: The desired motion mode
        """
        logging.debug(f"[CMD] setting motion: {motion}")
        cmd = (b'\x0f', f"MOTION : {motion}")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def set_transmission(self, transmission: str = "SLIDING"):
        """
            sets the desired transmission mode
        Args:
            transmission: the desired transmission mode. "SLIDING" or "BLOCK"
        """
        logging.debug(f"[CMD] setting transmission: {transmission}")
        cmd = (b'\x16', f"TRANSMISSION : {transmission}")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def set_antenna_range(self, range: float):
        """
            sets the antenna range by value (needs to be an allowed value of the instrument)
        """

        i = self.allowed_antenna_ranges.index(range)

        if i == 0:
            string = "FULL"
        else:
            string = f"ATN{i}"

        logging.debug(f"[CMD] setting antenna: TIA {string}")
        cmd = (b'\x11', f"SYSTEM : TIA {string}")

        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def set_antenna_range_index(self, i):
        """
            sets the antenna range by index
        """
        if i == 0:
            string = "FULL"
        else:
            string = f"ATN{i}"

        logging.debug(f"[CMD] setting antenna: TIA {string}")
        cmd = (b'\x11', f"SYSTEM : TIA {string}")

        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

    def set_acq_begin(self, t_begin: float = 1000.0):
        """
            sets the start time of the time domain window.
        Args:
            t_begin: The desired start time
        """
        logging.debug(f"[CMD] setting acq begin: {t_begin}")
        if t_begin < 10:
            b = b'\x18'
        elif t_begin < 100:
            b = b'\x19'
        else:
            b = b'\x1a'
        cmd = (b, f"ACQUISITION : BEGIN {t_begin:.1f}")
        measurement_was_running = self.acquisition
        # need to stop the measurement before changing the range
        logging.debug(f"stopping acquisition because of t_begin change! will restart late: {measurement_was_running}")
        self.range_changed.set()
        logging.debug(f"range changed set")
        self.set_acq_stop()
        logging.debug(f"stopped acq")
        self.cmd_queue.put(cmd)
        logging.debug(f"put cmd")
        self.cmd_ack.wait()
        logging.debug(f"wait for cmd ack")
        self.cmd_ack.clear()
        logging.debug(f"set t_begin")
        self.t_begin = t_begin
        logging.debug(f"waiting for buffer to be emptied")
        self.buffer_emptied.wait()
        self.buffer_emptied.clear()
        logging.debug(f"buffer is emptied")
        if measurement_was_running:
            # if the measurement was running, restart it
            self.set_acq_start()

    @staticmethod
    def nearest_entry(t_range: float, available_ranges: list):
        """

        Args:
            t_range: range provided by the user
            available_ranges: available ranges

        Returns: the nearest available range to the provided range

        """
        nearest = available_ranges[0]
        for num in available_ranges:
            if abs(t_range - num) < abs(t_range - nearest):
                nearest = num
        return nearest

    def set_acq_range(self, t_range: float = 50.0):
        """
            sets the range/width in the time domain window.
            available: 5, 10, 15, 20, 35, 50, 70, 100, 120, 150 or 200
        Args:
            t_range: The desired range
        """
        available_ranges = [5, 10, 15, 20, 35, 50, 70, 100, 120, 150, 200]
        if t_range not in available_ranges:
            logging.info(f"[CMD] {t_range} is not supported. Only {available_ranges} are supported.")
            t_range = self.nearest_entry(t_range, available_ranges)
        logging.debug(f"[CMD] setting acq range: {t_range}")
        if t_range <= 5.0:
            b = b'\x18'
        elif t_range <= 70.0:
            b = b'\x19'
        else:
            b = b'\x1a'
        cmd = (b, f"ACQUISITION : RANGE {t_range:.2f}")
        measurement_was_running = self.acquisition
        # need to stop the measurement before changing the range
        logging.debug(f"stopping acquisition because of range change! will restart late: {measurement_was_running}")
        self.range_changed.set()
        self.set_acq_stop()
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.range = t_range
        self.buffer_emptied.wait()
        self.buffer_emptied.clear()
        if measurement_was_running:
            # if the measurement was running, restart it
            self.set_acq_start()

    def set_acq_avg(self, avg: int = 2):
        """
            sets the width of the moving average to be performed by the device
        Args:
            avg: The desired averages
        """
        logging.debug(f"[CMD] setting acq avg: {avg}")
        if avg < 10:
            b = b'\x17'
        elif avg < 100:
            b = b'\x18'
        elif avg < 1000:
            b = b'\x19'
        else:
            b = b'\x1a'
        cmd = (b, f"ACQUISITION : AVERAGE {avg}")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        # reset the average after it was changed
        self.reset_acq_avg()
        self.avg = avg
        self.socket.avg_countdown = avg

    def reset_acq_avg(self):
        """
            resets the acquisition moving average to be performed by the device
        """
        logging.debug("[CMD] resetting acq avg")

        cmd = (b'\x17', "ACQUISITION : RESET AVG")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.socket.avg_countdown = self.avg

    def wait_for_avg(self):
        while self.socket.avg_countdown > 0:
            time.sleep(0.1)

    def set_laser(self, state: bool):
        """
            sets the laser mode ON or OFF
        Args:
            state: True for ON, False for OFF
        """
        if state:
            logging.debug("[CMD] setting laser on")
            cmd = (b'\x0a', "LASER : ON")
        else:
            # emitter bias must be turned off before we turn of the laser
            if self.emitter:
                self.set_emitter(1, False)
                self.set_emitter(2, False)
            logging.debug("[CMD] setting laser off")
            cmd = (b'\x0b', "LASER : OFF")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.laser = state

    def set_emitter(self, emitter: int, state: bool):
        """
            sets the state of the emitter ON or OFF
        Args:
            emitter: Emitter 1 or 2
            state: True for ON, False for OFF
        """
        if emitter not in [1, 2]:
            logging.info(f"emitter {emitter} is invalid, please use 1 or 2 as emitter value")
            return
        if state:
            # laser must be running before we turn on the emitter bias
            if not self.laser:
                self.set_laser(True)
            logging.debug(f"[CMD] setting emitter {emitter} on")
            cmd = (b'\x0a', f"VOLT{emitter} : ON")
        else:
            logging.debug(f"[CMD] setting emitter {emitter} off")
            cmd = (b'\x0b', f"VOLT{emitter} : OFF")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.emitter[emitter - 1] = state

    def set_acq_start(self):
        """
            start the acquisition (data streaming)
        """
        logging.debug("[CMD] starting acquisition")
        cmd = (b'\x13', "ACQUISITION : START")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.acq_running.set()
        self.acquisition = True

    def set_acq_stop(self):
        """
            stop the acquisition (data streaming)
        """
        logging.debug("[CMD] stopping acquisition")
        cmd = (b'\x12', "ACQUISITION : STOP")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.acq_running.clear()
        self.acquisition = False

    def auto_pulse_detection(self, lower: int, upper: int, detection_window: int = 100, detection_avg: int = 10):
        """

        Auto detection function of pulse.
        Spectrometer needs to be running (laser, emitter, acq) before calling this

        :param lower: lower end of detection window
        :param upper: upper end of detection window
        :param detection_window: detection window width
        :param detection_avg: detection avg to smooth out noise
        :return: detected pulse or None
        """

        previous_range = self.range
        previous_avg = self.avg
        logging.info(f"Searching pulses in range from {lower} to {upper}")

        # setup
        self.set_acq_range(detection_window)
        self.set_acq_avg(detection_avg)
        self.reset_acq_avg()
        detected_pulse = None

        # search in range
        for t_begin in range(lower, upper, detection_window):
            self.set_acq_begin(t_begin)
            self.reset_acq_avg()
            self.wait_for_avg()

            timestamp = self.get_data().time.astype(np.float32)
            pulse = self.get_data().signal_1.astype(np.float32)
            detected_pulse = detect_pulse(timestamp, pulse)
            if detected_pulse:
                # found a pulse
                logging.info(f"Found pulse at {detected_pulse}")
                self.set_acq_begin(detected_pulse)
                break

        # revert to previous settings
        self.set_acq_avg(previous_avg)
        self.set_acq_range(previous_range)

        # if no pulse has been detected, raise error
        if not detected_pulse:
            logging.error(f"No pulse detected in range from {lower} to {upper}")
            raise Exception(f"No pulse detected in the range from {lower} to {upper}")
