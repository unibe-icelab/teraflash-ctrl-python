from teraflash import TeraFlash

if __name__ == "__main__":
    with TeraFlash() as device:
        print(f"status: {device.get_status()}")
        print(device.get_data().signal_1)
