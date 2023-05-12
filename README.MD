# TeraFlash Pro Python Package

This code is developed by the University of Bern and is no official product of Toptica Photonics AG.  
This Python Package allows the configuration and readout of the TeraFlash Pro THz spectrometer.  
The TCP communication protocol is probably incomplete and features may be missing as it was reverse engineered using
wireshark. The scanning stage is not supported but a list of other features is.

This is a simple library with no persistence settings (the configurations of the previous run will not be stored when the python session is closed).
A complete GUI written in Rust is also available [here](https://spacegit.unibe.ch/teraflash/teraflash-ctrl).

Features:  
- [X] Select begin time for the time window
- [X] Select range
- [X] Select average
- [X] Start/Stop Laser
- [X] Start/Stop Emitters
- [X] Start/Stop Acquisition
- [X] Set transmission
- [X] Set motion mode
- [X] Set channel
- [X] Get status
- [X] Get data

  
- [ ] Set antenna
- [ ] Set sensitivity
- [ ] ...

## I. Installation
[Download](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/archive/main/teraflash-ctrl-python-main.zip) the zip archive from
this webpage and move it into your working directory and then run:
```shell
pip install teraflash-ctrl-python-main.zip
```
to install the package for your virtual python environment or system wide.

## II. Taking a measurement
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

Always use the context manager to ensure that the connection is properly closed upon exiting!  
Consult the [`example.py`](example.py) for usage.  
  
  
_Disclaimer: This package is provided on a best effort basis with no guarantee as to the functionality and correctness. Use at your
own risk.
Users are encouraged to contribute by submitting [issues](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/issues) and/or [merge requests](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/merge_requests) for bug reporting or feature requests._