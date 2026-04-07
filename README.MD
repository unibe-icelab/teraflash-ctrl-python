# TeraFlash Pro Python Package

[![PEP8](https://github.com/unibe-icelab/teraflash-ctrl-python/actions/workflows/format.yml/badge.svg)](https://github.com/unibe-icelab/teraflash-ctrl-python/actions/workflows/format.yml)
[![PyPI](https://img.shields.io/pypi/v/teraflash-ctrl?label=pypi%20package)](https://pypi.org/project/teraflash-ctrl/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/teraflash-ctrl)](https://pypi.org/project/teraflash-ctrl/)


<a href="https://github.com/unibe-icelab/teraflash-ctrl-python/releases"><img src="https://raw.githubusercontent.com/unibe-icelab/teraflash-ctrl-python/refs/heads/main/icons/icon.png" alt=“” width="100" height="100"> </img> </a>

This code is developed by the University of Bern and is no official product of Toptica Photonics AG.  
This Python Package allows the configuration and readout of the TeraFlash Pro THz spectrometer.  
The TCP communication protocol is probably incomplete and features may be missing as it was reverse engineered using
wireshark. The scanning stage is not supported but a list of other features is.

This is a simple library with no persistence settings (the configurations of the previous run will not be stored when the python session is closed).
A complete GUI written in Rust is also available [here](https://github.com/unibe-icelab/teraflash-ctrl).

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
Download from PyPi:
```shell
pip install teraflash-ctrl
```

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
Users are encouraged to contribute by submitting [issues](https://github.com/unibe-icelab/teraflash-ctrl-python/issues) and/or [pull requests](https://github.com/unibe-icelab/teraflash-ctrl-python/pulls) for bug reporting or feature requests._


Copyright (c) 2026 University of Bern, Space Research & Planetary Sciences, Linus Leo Stöckli.

This work is licensed under the Creative Commons
Attribution-NonCommercial 4.0 International License.
To view a copy of this license, visit
https://creativecommons.org/licenses/by-nc/4.0/