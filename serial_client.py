import sys, serial, random, struct, binascii, time

try:
	fd = sys.argv[1]
	dev = serial.Serial(fd, 19200, writeTimeout=1)
except IndexError:
	print "Please give me cookies...."
	exit()
except serial.SerialException:
	print "No such device: " + fd
	exit()

nodeid = random.randrange(1,5)
pkgnum = random.randrange(8,17)

args = ' '.join(sys.argv[2:])

chksum = 7 + len(args)

raw = struct.pack(">BIBB", chksum, nodeid, pkgnum, 17) + binascii.a2b_qp(args)

print "chksum:  " + str(chksum)
print "nodeid:  " + str(nodeid)
print "pkgnum:  " + str(pkgnum)
print "payload: " + args
print "------------"

i = 0

for c in binascii.b2a_hex(raw):
	sys.stdout.write(c)
	if (i % 2): sys.stdout.write(" ")
	i = i+1

print ""

time.sleep(0.1)

dev.write(raw)
dev.flush()

dev.close()