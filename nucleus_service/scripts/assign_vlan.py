#!/usr/bin/python
import sys, argparse, string, pexpect, comet_utils

TFTP_DIR = '/var/lib/tftpboot/'


parser = argparse.ArgumentParser()

parser.add_argument('--rack', type=int, required=True)
parser.add_argument('--vlan', type=int, required=True)
parser.add_argument('ports', nargs=argparse.REMAINDER, type=int)

args = parser.parse_args(sys.argv[1:])

if not args.ports:
    print'Need a list of ports'
    sys.exit(0)

for a in args.ports:
    if a < 3 or a > 64:
        print'Invalid port number, must be in the range 3-64'
        sys.exit(0)

args.ports = comet_utils.sort(args.ports)

interfaces = comet_utils.convertports(args.ports)

print ('SSHing to Switch')
child = pexpect.spawn('ssh 192.168.55.232')

child.expect('comet-rack32#')

print('Copying running config from switch')
child.sendline('copy running-config tftp://132.249.200.124/running-config')

child.expect('(y/n)')

child.send('y')

child.expect('File transfer operation completed successfully.')
print('Transfer Complete')

child.sendline('exit')

child.sendline('exit')

child.close()

print('Creating Scripts')
comet_utils.createscripts(args.vlan, interfaces)

# Transfer script to switch and apply here


#Verify changes
child = pexpect.spawn('ssh 192.168.55.232')

child.expect('comet-rack32#')

for a in interfaces:
    child.send('sh run ' + a)
    child.expect('comet-rack32#')
    print(child.before)

child.sendline('exit')
child.sendline('exit')

child.close()

print('Script Done')



