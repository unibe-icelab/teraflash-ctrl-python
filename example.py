import time

from teraflash import TeraFlash
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # use context manager!
    with TeraFlash(log_file="test.log") as device:
        print(f"status: {device.get_status()}")
        device.set_acq_begin(1100.0)  # optional, otherwise use default values
        device.set_acq_range(150.0)  # optional, otherwise use default values
        device.set_acq_avg(10)  # optional, otherwise use default values
        device.set_laser(True)
        device.set_emitter(1, True)
        device.set_acq_start()
        time.sleep(3)
        for i in range(10):
            data = device.get_data()
            print(data.signal_1)
            time.sleep(0.1)
        device.set_acq_stop()
        device.set_laser(False)
        device.set_emitter(1, False)

    data = device.get_data()
    print(data.signal_1)
    plt.plot(data.time, data.signal_1, color="black")
    plt.xlabel("time [ps]")
    plt.ylabel("amplitude [a.u.]")
    plt.title("Time Domain Pulse")
    plt.show()
