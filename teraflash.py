import logging
import queue
import threading
import time

import numpy as np

from interface import TopticaSocket


class DataContainer:

    def __init__(self, n=1000):
        self.time = np.zeros(n)

        self.signal_1 = np.zeros(n)
        self.freq_1 = np.zeros(n)
        self.freq_1_amp = np.zeros(n)
        self.freq_1_phase = np.zeros(n)

        self.signal_2 = np.zeros(n)
        self.freq_2 = np.zeros(n)
        self.freq_2_amp = np.zeros(n)
        self.freq_2_phase = np.zeros(n)


class TeraFlash:

    def __init__(self, ip: str = "169.254.84.101"):
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00\x00'
        self.send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
        self.r_stat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00'

        logging.basicConfig(filename=f"logs/teraflash_{int(time.time())}.log", level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler())

        self.ip = ip
        self.cmd_queue = queue.Queue()
        self.data = DataContainer()
        self.status = ""

        try:
            socket = TopticaSocket(self.ip, self.data, self.status)
        except ConnectionError:
            logging.error("[INIT] Device is not connected. Check cabling")
            return

        # launch tcp config socket
        config_thread = threading.Thread(target=socket.run_conf_tcp, args=(self.cmd_queue,))

        # launch tcp data socket
        data_thread = threading.Thread(target=socket.run_tcp_dat)

        data_thread.start()
        config_thread.start()

        self.setup()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()
        time.sleep(1)
        logging.debug("[EXIT] disconnected from device")

    def setup(self):
        """
            performs the setup of the device as reconstructed
            by using wireshark on the official application
        """

        logging.info("[INIT] setting up the device...")
        self.get_sys_status()
        self.get_sys_status()
        self.set_channel()
        self.set_mode()
        self.set_transmission()
        self.set_antenna()
        self.set_acq_begin()
        self.set_acq_avg()
        self.set_acq_stop()
        self.set_acq_range()
        self.get_sys_monitor()
        self.set_acq_avg()
        self.set_acq_range()
        self.get_sys_monitor()
        self.get_sys_status()
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

    def get_sys_monitor(self):
        """
            this is repeatedly called in the official application
        """
        cmd = (b'\x12', "SYSTEM : MONITOR 1")
        self.cmd_queue.put(cmd)

    def set_channel(self, channel: str = "D"):
        """
            sets dual or single channel mode
        Args:
            channel: The desired mode
        """
        logging.debug(f"[CMD] setting channel: {channel}")
        cmd = (b'\x0b', f"CHANNEL : {channel}")
        self.cmd_queue.put(cmd)

    def set_mode(self, motion: str = "NORMAL"):
        """
            sets the motion mode
        Args:
            motion: The desired motion mode
        """
        logging.debug(f"[CMD] setting motion: {motion}")
        cmd = (b'\x0f', f"CHANNEL : {motion}")
        self.cmd_queue.put(cmd)

    def set_transmission(self, transmission: str = "SLIDING"):
        """
            sets the desired transmission mode
        Args:
            transmission: the desired transmission mode. "SLIDING" or "BLOCK"
        """
        logging.debug(f"[CMD] setting transmission: {transmission}")
        cmd = (b'\x16', f"TRANSMISSION : {transmission}")
        self.cmd_queue.put(cmd)

    def set_antenna(self):
        """
            sets the antenna mode. TBD if this can be adjusted or is fixed.
        """
        logging.debug("[CMD] setting antenna: TIA ATN2")
        cmd = (b'\x11', "SYSTEM : TIA ATN2")
        self.cmd_queue.put(cmd)

    def set_acq_begin(self, t_begin: float = 1000.0):
        """
            sets the start time of the time domain window.
        Args:
            t_begin: The desired start time
        """
        logging.debug(f"[CMD] setting acq begin: {t_begin}")
        if t_begin < 10:
            b = b'0x18'
        elif t_begin < 100:
            b = b'0x19'
        else:
            b = b'0x1a'
        cmd = (b, f"ACQUISITION : BEGIN {t_begin:.1f}")
        self.cmd_queue.put(cmd)

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
        Args:
            t_range: The desired range
        """
        available_ranges = [5, 10, 15, 20, 35, 50, 70, 100, 120, 150, 200]
        if t_range not in available_ranges:
            logging.info(f"[CMD] {t_range} is not supported. Only {available_ranges} are supported.")
            t_range = self.nearest_entry(t_range, available_ranges)
        logging.debug(f"[CMD] setting acq range: {t_range}")
        if t_range <= 5.0:
            b = b'0x18'
        elif t_range <= 70.0:
            b = b'0x19'
        else:
            b = b'0x1a'
        cmd = (b, f"ACQUISITION : RANGE {t_range:.2f}")
        self.cmd_queue.put(cmd)

    def set_acq_avg(self, avg: int = 2):
        """
            sets the width of the moving average to be performed by the device
        Args:
            avg: The desired averages
        """
        logging.debug(f"[CMD] setting acq avg: {avg}")
        if avg < 10:
            b = b'0x17'
        elif avg < 100:
            b = b'0x18'
        elif avg < 1000:
            b = b'0x19'
        else:
            b = b'0x1a'
        cmd = (b, f"ACQUISITION : AVERAGE {avg}")
        self.cmd_queue.put(cmd)

    def reset_acq_avg(self):
        """
            resets the acquisition moving average to be performed by the device
        """
        logging.debug("[CMD] resetting acq avg")

        cmd = (b'0x17', "ACQUISITION : RESET AVG")
        self.cmd_queue.put(cmd)

    def set_laser(self, state: bool):
        """
            sets the laser mode ON or OFF
        Args:
            state: True for ON, False for OFF
        """
        if state:
            logging.debug("[CMD] setting laser on")
            cmd = (b'0x0a', "LASER : ON")
        else:
            logging.debug("[CMD] setting laser off")
            cmd = (b'0x0b', "LASER : OFF")
        self.cmd_queue.put(cmd)

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
            logging.debug(f"[CMD] setting emitter {emitter} on")
            cmd = (b'0x0a', f"VOLT{emitter} : ON")
        else:
            logging.debug(f"[CMD] setting emitter {emitter} off")
            cmd = (b'0x0b', f"VOLT{emitter} : OFF")
        self.cmd_queue.put(cmd)

    def set_acq_start(self):
        """
            start the acquisition (data streaming)
        """
        logging.debug("[CMD] starting acquisition")
        cmd = (b'0x13', "ACQUISITION : START")
        self.cmd_queue.put(cmd)

    def set_acq_stop(self):
        """
            stop the acquisition (data streaming)
        """
        logging.debug("[CMD] stopping acquisition")
        cmd = (b'0x12', "ACQUISITION : STOP")
        self.cmd_queue.put(cmd)
