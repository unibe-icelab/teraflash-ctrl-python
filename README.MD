# TeraFlash Pro Python Package

This code is developed by the University of Bern and is no official product of Toptica Photonics AG.  
The TCP communication protocol is probably incomplete and features may be missing as it was reverse engineered using
wireshark. The scanning stage is not supported but a list of other features is.

A complete GUI written in Rust is also available [here](https://spacegit.unibe.ch/teraflash/teraflash-ctrl).

Always use the context manager to make sure that the connection is properly closed:
```python
from teraflash import TeraFlash

if __name__ == "__main__":
    
    ip = "169.254.84.101"
    with TeraFlash(ip) as device:
        print(device.get_status())
```

## Taking a measurement
After connecting to the device, you can turn on the laser and then the emitter.
After starting the acquisition, new data should be continuously updated and the most recent dataset can be obtained using `device.get_data()`:
```python
from teraflash import TeraFlash

if __name__ == "__main__":
    
    ip = "169.254.84.101"
    with TeraFlash(ip) as device:
        print(device.get_status())
        device.set_laser(True)
        device.set_emitter(1, True)
        device.set_acq_start()
        print(device.get_data())
```

  
  
_Disclaimer: This package is provided on a best effort basis with no guarantee as to the functionality and correctness. Use at your
own risk.
Users are encouraged to contribute by submitting [issues](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/issues) and/or [merge requests](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/merge_requests) for bug reporting or feature requests._