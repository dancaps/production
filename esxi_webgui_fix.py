#! /usr/bin/python
import shutil, os

src_file = '/etc/vmware/rhttpproxy/endpoints.conf'
bck_file = '/etc/vmware/rhttpproxy/endpoints.conf.backup'

#copy file
try:
    shutil.copyfile(src_file, bck_file)
except:
    print 'There was a problem creating a backup of the file'

#remove the line
fhandler = open(src_file, 'r')
file = fhandler.readlines()
fhandler.close()
fhandler = open(src_file, 'w')

for line in file:
    if line.startswith('/ui'):
        continue
    fhandler.write(line)
