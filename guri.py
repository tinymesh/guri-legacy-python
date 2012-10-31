from datetime import datetime, date, time

import sys
import os
import socket
import serial
import binascii
import time
import struct
import threading

from twisted.internet import protocol, reactor


try:
	True
except NameError:
	True = 1
	False = 0

class ProxyClient(protocol.Protocol):
	args    = None
	device  = None
	channel = None
	alive   = False

	def connectionMade(self):
		if self.args.flow:
			self.device.setRTS()
		self.alive = True
		self.channel = threading.Thread(target = self.reader)
		self.channel.setDaemon(True)
		self.channel.setName('serial -> tcp')
		self.channel.start()

	def dataReceived(self, buf):
		while True:
			if not self.args.flow or self.device.getCTS():
				self.device.write(buf)
				break
		self.log_payload(buf, "<<", 3);

	def connectionLost(self, reason):
		if self.args.flow:
			self.device.setRTS(False)
		self.alive = False
		self.channel.join(5)
		self.log("client connection terminated: %s" % reason.value)

	def reader(self):
		self.log("starting serial thread")
		buf = ""
		while self.alive:
			buf = self.device.read(1)
			time.sleep(0.02)
			n = self.device.inWaiting()
			if n:
				buf += self.device.read(n)
			self.log_payload(buf, ">>", 1)
			self.transport.write(buf)
		self.alive = False
		self.log("ending serial thread")

		return buf

	def log(self, buf):
		if self.args.verbose >= 1:
			sys.stderr.write("--- %s ---\n" % (buf))

	def log_payload(self, buf, prompt, lvl):
		i = 0
		if self.args.verbose >= lvl:
			sys.stdout.write("%s %s: " %(prompt, str(datetime.now())))
			for c in binascii.b2a_hex(buf):
				sys.stdout.write(c)
				if (i % 2): sys.stdout.write(" ")
				i = i+1
			sys.stdout.write("\n")

class ProxyFactory(protocol.ReconnectingClientFactory):
	protocol = ProxyClient

	def __init__(self, args, device):
		self.maxDelay     = 5
		self.initialDelay = 1
#		if -1 != args.retries:
#			self.maxRetries = args.retries
		self.args   = args
		self.device = device

	def buildProtocol(self, addr):
		self.resetDelay()
		proto = self.protocol()
		proto.args   = self.args
		proto.device = self.device
		return proto

	def clientConnectionFailed(self, connector, reason):
		sys.stderr.write("--- connection failed (%s) ---\n" %(reason.value))
		protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

	def clientConnectionLost(self, connector, reason):
		sys.stderr.write("--- connection lost (%s) ---\n" % (reason.value))
		protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(
		prog        = 'Guri connector',
		description = 'TTY to TCP/IP redirection',
		add_help    = True)
	parser.add_argument('device',
		metavar  = '<device>',
		help     = 'The serial device to communicate with')
	parser.add_argument('host',
		metavar  = '<remote-host>',
		help     = 'Remote host to connect to')
	parser.add_argument('--retries',  '-t',
		metavar  = '<tries>',
		default  = -1,
		dest     = 'retries',
		type     = int,
		help     = 'Number of times to retry, -1 equals infinit tries. Defaults to %(default)s')
	parser.add_argument('--port',  '-p',
		metavar  = '<port>',
		default  = 7000,
		dest     = 'port',
		help     = 'Remote port')
	parser.add_argument('--baudrate', '-r',
		dest    = 'baudrate',
		type    = int,
		help    = "Set baudrate, defaults to %(default)s",
		default = 19200,
		metavar = '<rate>')
	parser.add_argument('--parity',
		metavar = '<parity>',
		default = 'N',
		help = "Set bit parity, one of [N, E, O], defaults to %(default)s",
		)
	parser.add_argument('--xonoff',
		default = False,
		action  = 'store_true',
		help = "Enable XON/XOF software flow control"
		)
	parser.add_argument('--flow', '-f',
		default = False,
		action  = 'store_true',
		help = "Enable hardware flow control"
		)
	parser.add_argument('--verbose', '-v',
		action = 'count',
		help   = 'Increase verbosity. Default is only show errors, -v show messages from downstream, -vv shows upstream/downstream -vvv adds a timestamp')
	parser.add_argument('--version', '-V', action='version', version='%(prog)s 1.0')

	options = parser.parse_args()

	# connect to serial port
	ser = serial.Serial()
	ser.port	 = options.device
	ser.baudrate = options.baudrate
	ser.parity   = options.parity
	ser.xonxoff  = options.xonoff
	ser.rtscts   = options.flow
	ser.timeout  = 1	 # required so that the reader thread can exit

	if options.verbose > 0:
		sys.stderr.write("--- Serial to TCP redirect --- Ctrl-C / BREAK to quit\n")
		sys.stderr.write("--- %s %s,%s,%s,%s ---\n" % (ser.portstr, ser.baudrate, 8, ser.parity, 1))

	try:
		ser.open()
	except serial.SerialException, e:
		sys.stderr.write("Could not open serial port %s: %s\n" % (ser.portstr, e))
		sys.exit(1)

	factory = ProxyFactory(options, ser)
	reactor.connectTCP(options.host, options.port, factory, timeout = 1)
	reactor.run()
