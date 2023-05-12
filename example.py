import time

from teraflash import TeraFlash
import matplotlib.pyplot as plt


if __name__ == "__main__":
    with TeraFlash(log_file="test.log") as device:
        print(f"status: {device.get_status()}")
        device.set_acq_begin(1100.0)
        device.set_acq_range(150.0)
        device.set_laser(True)
        device.set_emitter(1, True)
        device.set_acq_avg(10)
        device.set_acq_start()
        # wait some time to gather data
        time.sleep(1)
        print(device.get_data().signal_1)
        device.set_acq_stop()
        device.set_laser(False)
        device.set_emitter(1, False)

    print(device.get_data().signal_1)
    plt.plot(device.get_data().time, device.get_data().signal_1)
    plt.show()

