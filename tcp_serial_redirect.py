from datetime import datetime, date, time

import sys
import os
import socket
import serial
import binascii
import time 
import struct

try:
    True
except NameError:
    True = 1
    False = 0

if __name__ == '__main__':
    import optparse

    parser = optparse.OptionParser(
        usage = "%prog [options] [port [baudrate]]",
        description = "Serial -> TCP/IP redirect",
        epilog = """\
Takes a serial connection and transfers data in a timely manner to a remote network service
""")

    parser.add_option("-q", "--quiet",
        dest = "quiet",
        action = "store_true",
        help = "suppress non error messages",
        default = False
    )

    parser.add_option("-s", "--sniff",
        dest = "sniff",
        action = "store_true",
        help = "Sniff packages that goes through",
        default = False
    )

    group = optparse.OptionGroup(parser,
        "Serial Port",
        "Serial port settings"
    )
    parser.add_option_group(group)

    group.add_option("-d", "--device",
        dest = "device",
        help = "device name",
        default = None
    )

    group.add_option("-b", "--baud",
        dest = "baudrate",
        action = "store",
        type = 'int',
        help = "set baud rate, default: %default",
        default = 19200
    )

    group.add_option("", "--parity",
        dest = "parity",
        action = "store",
        help = "set parity, one of [N, E, O], default=%default",
        default = 'N'
    )

    group = optparse.OptionGroup(parser,
        "Network settings",
        "Network configuration."
    )
    parser.add_option_group(group)

    group.add_option("-p", "--port",
        dest = "port",
        action = "store",
        type = 'int',
        help = "TCP port to connect to",
        default = 7001
    )

    (options, args) = parser.parse_args()

    # get port and baud rate from command line arguments or the option switches
    device = options.device
    baudrate = options.baudrate
    if args:
        if options.device is not None:
            parser.error("no arguments are allowed, options only when --device is given")
        port = args.pop(0)
        if args:
            try:
                baudrate = int(args[0])
            except ValueError:
                parser.error("baud rate must be a number, not %r" % args[0])
            args.pop(0)
        if args:
            parser.error("too many arguments")
    else:
        if device is None: device = 0

    # connect to serial port
    ser = serial.Serial()
    ser.port     = port
    ser.baudrate = baudrate
    ser.parity   = options.parity
    ser.timeout  = 1     # required so that the reader thread can exit

    if not options.quiet:
        sys.stderr.write("--- Serial to TCP redirect --- Ctrl-C / BREAK to quit\n")
        sys.stderr.write("--- %s %s,%s,%s,%s ---\n" % (ser.portstr, ser.baudrate, 8, ser.parity, 1))

    try:
        ser.open()
    except serial.SerialException, e:
        sys.stderr.write("Could not open serial port %s: %s\n" % (ser.portstr, e))
        sys.exit(1)
    
    mark = time.time()
    diff = 0
    data = ""

    while True:
        if len(data) == 0:
            diff = 0
        else:
            diff = (time.time() - mark)

        try:
            data += ser.read(ser.inWaiting())

            if data and (diff > 5 or int(binascii.b2a_hex(data[0]), 16) == len(data)):
                if options.sniff:
                    sys.stdout.write(str(datetime.now()) + ": ")
                    i = 0

                    for c in binascii.b2a_hex(data):
                        sys.stdout.write(c)
                        if (i % 2): sys.stdout.write(" ")
                        i = i+1

                    print ""

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(("127.0.0.1", options.port))
                sock.send(data)
                sock.close()

                mark = time.time()
                data = ""
                ser.flush()

        except KeyboardInterrupt:
            break
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            data = ""
            diff = 0
            break

    sys.stderr.write('\n--- exit ---\n')

