import logging
import queue
import threading
import time
from wakepy import set_keepawake, unset_keepawake
import os

from interface import TopticaSocket
import interface


class TeraFlash:

    def __init__(self,
                 ip: str = "169.254.84.101",
                 rng: int = 50,
                 t_begin: float = 1000.0,
                 avg: int = 2,
                 log_file = None):
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
        self.cmd_ack.clear()
        self.connected.clear()
        self.running.set()
        self.buffer_emptied.set()
        self.range_changed.clear()
        self.acq_running.clear()

        try:
            socket = TopticaSocket(self.ip, self.running, self.connected, self.cmd_ack, self.buffer_emptied,
                                   self.range_changed, self.acq_running)
        except ConnectionError:
            logging.error("[INIT] Device is not connected. Check cabling")
            exit()

        # keep the computer awake
        try:
            set_keepawake(keep_screen_awake=True)
        except:
            pass

        # configure tcp config socket
        self.config_thread = threading.Thread(target=socket.run_conf_tcp, args=(self.cmd_queue,))

        # configure tcp data socket
        self.data_thread = threading.Thread(target=socket.run_tcp_dat, args=(self.cmd_queue,))

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
        # clear the keep-awake flag
        try:
            unset_keepawake()
        except:
            pass
        logging.debug("[EXIT] disconnected from device")

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
        self.set_channel()
        self.set_mode()
        self.set_transmission()
        self.set_antenna()
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

    def set_antenna(self):
        """
            sets the antenna mode. TBD if this can be adjusted or is fixed.
        """
        logging.debug("[CMD] setting antenna: TIA ATN2")
        cmd = (b'\x11', "SYSTEM : TIA ATN2")
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
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()
        self.t_begin = t_begin

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

    def reset_acq_avg(self):
        """
            resets the acquisition moving average to be performed by the device
        """
        logging.debug("[CMD] resetting acq avg")

        cmd = (b'\x17', "ACQUISITION : RESET AVG")
        self.cmd_queue.put(cmd)
        self.cmd_ack.wait()
        self.cmd_ack.clear()

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
