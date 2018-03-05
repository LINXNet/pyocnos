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
>>> device.close()
```

### Reading config
```python
>>> from pyocnos import OcNOS
>>> device = OcNOS(hostname='192.168.1.222', username='admin', password='admin', timeout=10)
>>> device.open()
>>> running_config = device.get_running_config()
>>> device.close()
```

### Load Candidate config
```python
>>> from pyocnos import OcNOS
>>> device = OcNOS(hostname='192.168.1.222', username='admin', password='admin', timeout=10)
>>> device.open()
>>> # from a string
>>> device.load_candidate_config(config='test config')
>>> # Or could also be loaded from a file path
>>> device.load_candidate_config(filename='path-to-file.xml')
>>> device.close()
```
### Commit Candidate config
```python
>>> from pyocnos import OcNOS
>>> device = OcNOS(hostname='192.168.1.222', username='admin', password='admin', timeout=10)
>>> device.open()
>>> device.load_candidate_config(config='test config')
>>> # device running config will be replace by the candidate config
>>> device.commit_config() 
>>> device.close()
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