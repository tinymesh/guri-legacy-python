from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from serial.serialutil import SerialException
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.python import log
import sys

log.startLogging(sys.stdout)

client_list = []

class SerialClient(Protocol):
	def __init__(self, network, options):
		self.options = options
		self.network = network
		self.buf     = ""
		self.timeout = 0.02
		self.timer   = reactor.callLater(self.timeout, self.flushBuf)

	def connectionFailed(self):
		if self.options.verbose >= 2:
			log.err("-- connection to serial device failed ---")
		reactor.stop()

	def connectionMade(self):
		if self.options.verbose >= 2:
			log.msg("-- connected to serial device ---")

	def dataReceived(self, data):
		if not self.timer.active():
			self.timer   = reactor.callLater(self.timeout, self.flushBuf)
		self.buf += data

	def flushBuf(self):
		if "" != self.buf:
			if not self.network.connected:
				log.err("!! received data, but not connected to TCP/IP endpoint")
			else:
				if options.verbose >= 1:
					log.msg("<< data: ", " ".join([hex(ord(c))[2:].zfill(2) for c in self.buf]))
				self.network.notifyAll(self.buf)
				self.buf = ""

class NetworkClient(Protocol):
	options = None

	def connectionMade(self):
		if self.options.verbose >= 2:
			log.msg("-- tcp client connected")
		client_list.append(self)

	def dataReceived(self, data):
		if options.verbose >= 1:
			log.msg("<< ", " ".join([hex(ord(c))[2:].zfill(2) for c in self.buf]))

	def connectionLost(self, reason):
		if self.options.verbose >= 2:
			log.err("-- tcp client disconnected (%s)" % reason.value)
		if self in client_list:
			client_list.remove(self)

	def notifyClient(self, data):
		self.transport.write(data)

class NetworkClientFactory(ReconnectingClientFactory):
	protocol = NetworkClient

	def __init__(self, options):
		self.options = options
		self.connected = False
		client_list = []

	def buildProtocol(self, addr):
		self.connected = True
		self.resetDelay()
		proto = self.protocol()
		proto.options = self.options
		return proto

	def clientConnectionFailed(self, connector, reason):
		self.connected = False
		if self.options.verbose >= 2:
			log.err("-- tcp connection failed (%s) ---\n" % (reason.value))
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

	def clientConnectionLost(self, connector, reason):
		self.connected = False
		if self.options.verbose >= 2:
			log.err("-- tcp connection lost (%s) ---\n" % (reason.value))
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def notifyAll(self, data):
		for socket in client_list:
			socket.transport.write(data)

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

	parser.add_argument('--verbose', '-v',
		action = 'count',
		help   = 'Increase verbosity. Default is only show errors, -v show messages from downstream, -vv shows upstream/downstream -vvv adds a timestamp')
	parser.add_argument('--version', '-V', action='version', version='%(prog)s 1.0')

	options = parser.parse_args()

	factory = NetworkClientFactory(options)
	factory.noisy = True if options.verbose >= 3 else False
	reactor.connectTCP(options.host, options.port, factory)
	try:
		SerialPort(SerialClient(factory, options), options.device, reactor, baudrate=options.baudrate)
		reactor.run()
	except SerialException, e:
		log.err("Could not open serial device %s" % options.device)
		log.err("Error: %s" % e)
		sys.exit(1)
