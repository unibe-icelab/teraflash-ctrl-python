from teraflash import TeraFlash

if __name__ == "__main__":

    with TeraFlash() as device:
        print(device.data)
