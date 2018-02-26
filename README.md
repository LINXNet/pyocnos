# pyocnos
Python library to remotely manage/automate switches running OcNOS operating system.

## Requirments

### Python
* ncclient = 0.5.3

### Install via pip
```bash
pip install pyocnos
```

### Upgrade via pip
```bash
pip install --upgrade pyocnos
```



## Documentation

### Connect to remote device
```python
>>> from pyocnos import OcNOS
>>> device = OcNOS(hostname='192.168.1.222', username='admin', password='admin', timeout=10)
>>> device.open()
```

### Logging
Logging is facilitated though the python logging module. Once you initilize a logger in your main program,
pyexos will emit its messages accordingly.
```python
>>> import logging
>>> import sys
>>> logging.basicConfig(stream=sys.stdout, level=logging.INFO)
```

## License

Copyright 2018 LINX

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0