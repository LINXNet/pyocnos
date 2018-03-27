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
>>> from pyocnos.ocnos import OCNOS
>>> # initialze device
>>> # timeout is optional default value is 60 seconds
>>> device = OCNOS(hostname='hostname', username='username', password='password', timeout=10)
>>> # open connection
>>> device.open()
>>> # check if connection is alive
>>> device.is_alive() # returns True
>>> # close the connection
>>> device.close()
```
### Connect to remote device using context
```python
>>> from pyocnos.ocnos import OCNOS
>>> # initialze device and open connection
>>> with OCNOS(hostname='hostname', username='username', password='password') as device:
>>>     device.is_alive() # returns True
```

### Reading config
```python
>>> from pyocnos.ocnos import OCNOS
>>> # initialze device and open connection
>>> with OCNOS(hostname='hostname', username='username', password='password') as device:
>>>     running_config = device.get_running_config()
>>>     print(running_config)
```

### Load Candidate config
```python
>>> from pyocnos.ocnos import OCNOS
>>> # initialze device and open connection
>>> with OCNOS(hostname='hostname', username='username', password='password') as device:
>>>     # from a string
>>>     device.load_candidate_config(config='<config><vr><vrf>2</vrf></vr></config>')
>>>     # Or could also be loaded from a file path
>>>     device.load_candidate_config(filename='path-to-file.xml')
```

### Diff Candidate and Running config
```python
>>> from pyocnos.ocnos import OCNOS
>>> # initialze device and open connection
>>> with OCNOS(hostname='hostname', username='username', password='password') as device:
>>>     device.load_candidate_config(config='<config><vr><vrf>2</vrf></vr></config>')
>>>     #Now we can diff the candidate with the running
>>>     diff = device.compare_config()
>>>     for line in diff:
>>>         print(line)
>>> # Should print something like
>>> # [vr]
>>> #  - <vrf>1</vrf>
>>>>#  + <vrf>2</vrf>
```


### Commit Candidate config
```python
>>> from pyocnos.ocnos import OCNOS
>>> # initialze device and open connection
>>> with OCNOS(hostname='hostname', username='username', password='username') as device:
>>>     # load candidate config from a string
>>>     device.load_candidate_config(config='<config><vr><vrf>2</vrf></vr></config>')
>>>     # device running config will be replace by the candidate config
>>>     device.commit_config()
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