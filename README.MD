# TeraFlash Python Package

This code is developed by the University of Bern and is no official product of Toptica Photonics AG.  
The TCP communication protocol is probably incomplete and features may be missing as it was reverse engineered using
wireshark.

A complete GUI written in Rust is also available [here](https://spacegit.unibe.ch/teraflash/teraflash-ctrl).

Always use the context manager to make sure that the connection is properly closed:
```python
from teraflash import TeraFlash

if __name__ == "__main__":
    
    ip = "169.254.84.101"
    with TeraFlash(ip) as device:
        print(device.status)
        print(device.data)
```

alternatively you can close the connection yourself - but you need to make sure to do so,
to prevent from damaging the TeraFlash Spectrometer

```python
from teraflash import TeraFlash

if __name__ == "__main__":

    device = TeraFlash()
    print(device.status)
    print(device.data)
    device.disconnect()
```

_Disclaimer: This package is provided on a best effort basis with no guarantee as to their functionality and correctness. Use at your
own risk.
Users are encouraged to contribute by submitting issues and/or merge requests for bug reporting or feature requests._