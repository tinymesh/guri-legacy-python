# GURI - RS232-TCP/IP gateway

Simple proxy for serial port to TCP/IP, used mainly for testing out
Tinymesh Cloud on your local machine.

```
usage: guri.py [-h] [--port <port>] [--baudrate <rate>] [--verbose] <device> <remote-host>

positional arguments:
  <device>              The serial device to communicate with
  <remote-host>         Remote host to connect to

optional arguments:
  -h, --help            show this help message and exit
  --port <port>, -p <port>
                        Remote port
  --baudrate <rate>, -r <rate>
                        Set baudrate, defaults to 19200
  --verbose, -v         Increase verbosity. Default is only show errors, -v
                        show messages from downstream, -vv shows
                        upstream/downstream -vvv adds a timestamp
  --version, -V         show program's version number and exit
```

## Example
```bash
# Connecting to Tinymesh cloud
C:\python27\python2.exe guri.py COM27 cloud.tiny-mesh.com -p 7001
```

## Installing on windows

There is currently one-click way to install on windows, to make it
work you need the following dependencies:

+ Download and install `python-2.7` http://python.org/download/
+ Download and install `pyWin32` http://sourceforge.net/projects/pywin32/files/
+ Download and install `twisted` http://twistedmatrix.com/trac/wiki/Downloads
+ Download https://pypi.python.org/pypi/pyserial (you must manually run the install file found in the archive)

## Installing on Linux

You should find packages for `twisted` and `pyserial` in your package
management tools.

## Licensing

GURI is released under a 2-clause BSD license. A copy of this license
can be found in the `./LICENSE` file.

Additionally the application dependencies uses the following licenses:

+ Python:     PSF - http://docs.python.org/2/license.html
+ Twisted:    MIT license - http://www.opensource.org/licenses/mit-license.php
+ pySerial    http://pyserial.sourceforge.net/appendix.html#license
