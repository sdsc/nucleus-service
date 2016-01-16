# Utility functions for Python Scripts
import sys, string

TFTP_DIR = '/var/lib/tftpboot/'

def createscript( vlan, interfaces ):
    name = 'dell_script.txt'

    try:
        file = open(name,'w')
        file.write('configure\n')
        for a in interfaces:
            file.write(a)
            file.write('switchport access vlan %d\n' %vlan)
            file.write('exit\n')

        file.close()
    except:
        print('Error')
        sys.exit(0)

def createscripts( vlan, interfaces ):
    name = 'dell_script.txt'

    try:
        new_config = open(name,'w')
        backup_config = open('backup-config', 'w')
        new_config.write('configure\n')
        backup_config.write('configure\n')
        with open(TFTP_DIR + 'running-config', 'rb') as prev_config:
           i = 0
           while True:
               line = prev_config.readline()
               if not line: break
               if line == interfaces[i]:
                   backup_config.write(line)
                   new_config.write(interfaces[i])
                   new_config.write('switchport access vlan %d\n' %vlan)
                   new_config.write('exit\n')
                   while True:
                       line = prev_config.readline()
                       if line.startswith('switchport access vlan'):
                           backup_config.write(line)
                           backup_config.write('exit\n')
                           break
                   i += 1
               if i >= len(interfaces): break

    except:
        print('Error')
        sys.exit(0)

def sort( array ):
    less = []
    equal = []
    greater = []

    if len(array) > 1:
        pivot = array[0]
        for x in array:
            if x < pivot:
                less.append(x)
            if x == pivot:
                equal.append(x)
            if x > pivot:
                greater.append(x)

        return sort(less)+equal+sort(greater)

    else:
        return array

def convertports( ports ):
    interfaces = []
    for a in ports:
        if a <= 56 and a > 2:
            interfaces.append('interface Te1/0/%d\n' %a)
        elif a > 56 and a < 64:
            a = a % 8
            interfaces.append('interface Te1/1/%d\n' %a)
        elif a == 64:
            interfaces.append('interface Te1/1/8\n')

    return interfaces
