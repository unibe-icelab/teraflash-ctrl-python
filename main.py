import time

from teraflash import TeraFlash
import matplotlib.pyplot as plt


if __name__ == "__main__":
    with TeraFlash() as device:
        print(f"status: {device.get_status()}")

        device.set_laser(True)
        device.set_emitter(1, True)
        device.set_acq_start()
        # wait some time to gather data
        time.sleep(1)
        print(device.get_data().signal_1)

    plt.plot(device.get_data().time, device.get_data().signal_1)
    plt.show()

