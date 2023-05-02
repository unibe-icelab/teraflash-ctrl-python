# TeraFlash Python Package

This code is developed by the University of Bern and is no official product of Toptica Photonics AG.  
The TCP communication protocol is probably incomplete and features may be missing as it was reverse engineered using
wireshark.

Always use the context manager to make sure that the connection is properly closed:
```python
from teraflash import TeraFlash

if __name__ == "__main__":

    with TeraFlash() as device:
        print(device.status)
        print(device.data)
```

_Disclaimer: This package is provided on a best effort basis with no guarantee as to their functionality and correctness. Use at your
own risk.
Users are encouraged to contribute by submitting issues and/or merge requests for bug reporting or feature requests._