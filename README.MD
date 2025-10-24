# TeraFlash Pro Python Package

<a href="https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/releases"><img src="icons/icon.png" alt=“” width="100" height="100"> </img> </a>

This code is developed by the University of Bern and is no official product of Toptica Photonics AG.  
This Python Package allows the configuration and readout of the TeraFlash Pro THz spectrometer.  
The TCP communication protocol is probably incomplete and features may be missing as it was reverse engineered using
wireshark. The scanning stage is not supported but a list of other features is.

This is a simple library with no persistence settings (the configurations of the previous run will not be stored when the python session is closed).
A complete GUI written in Rust is also available [here](https://spacegit.unibe.ch/teraflash/teraflash-ctrl).

Features:  
- [x] Select begin time for the time window
- [x] Select range
- [x] Select average
- [x] Start/Stop Laser
- [x] Start/Stop Emitters
- [x] Start/Stop Acquisition
- [x] Set transmission
- [x] Set motion mode
- [x] Set channel
- [x] Get status
- [x] Get data (time domain and frequency domain)
- [x] auto pulse detection function
- [X] Set antenna range
- [ ] ...

## I. Installation
Download the [latest release](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/releases) or the [current state](https://spacegit.unibe.ch/teraflash/teraflash-ctrl-python/-/archive/main/teraflash-ctrl-python-main.zip)
as a zip archive, move it into your working directory and then run:
```shell
pip install teraflash-ctrl-python-v1.3.0.zip
```
for the latest version or
```shell
pip install teraflash-ctrl-python-main.zip
```
for the current state of the main branch to install the package for your virtual python environment or system-wide.

## II. Taking a measurement
When connected to the device, you can turn on the laser and then the emitter.
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