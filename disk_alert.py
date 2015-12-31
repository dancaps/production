#! /usr/bin/python

import smtplib, os

#if used space is >= this variable amount an alert will be sent
percent_threshold = 1
#empty message
msg = ''
#add the filesystem name to the exclusion list if you need it ignored
exclusion = ['/dev/sr0']

def get_hostname():
    #returns the hostname
    hostname = os.popen("hostname").readlines()
    return str(hostname[0])

def get_filesystem():
    #runs the df command and parses the data line by line from left to right and returns a list of lists
    #example [filesystem name, size of partition, space used, space available, used %]
    list_of_lines = os.popen("df").readlines()
    disk_info = []
    for i in list_of_lines:
        line = i
        filesystem_pos = line.find(' ')
        filesystem = line[:filesystem_pos]
        line = line[filesystem_pos + 1:]
        line = line.lstrip()
        size_pos = line.find(' ')
        size = line[:size_pos]
        line = line[size_pos + 1:]
        line = line.lstrip()
        used_pos = line.find(' ')
        used = line[:used_pos]
        line = line[used_pos + 1:]
        line = line.lstrip()
        avail_pos = line.find(' ')
        avail = line[:avail_pos]
        line = line[avail_pos + 1:]
        line = line.lstrip()
        use_pos = line.find(' ')
        use = line[:use_pos - 1]
        line = line[use_pos + 1:]
        line = line.lstrip()
        mounted_pos = line.find(' ')
        mounted = line[:mounted_pos]
        if filesystem == 'Filesystem' or size == '':
            continue
        disk_info.append([filesystem, int(size), int(used), int(avail), int(use)])
    return disk_info

def low_disk(disk_info):
    #determines if the used disk space is higher than the alert threshold and returns true or false
    if disk_info[4] >= percent_threshold:
        return True
    else:
        return False

def send_mail(usr_msg):
    #creates and sends email through the markit smtp server
    usr_smtp_server = 'appsmtp1.markit.partners'
    usr_to = 'MK-GTSSolutionsEngineeringVirtualization@markit.com'
    usr_from = 'vcs-bld1@markit.com'
    usr_subject = 'TEST EMAIL:: LOW DISK SPACE ALERT ON ' + str(get_hostname()).upper()

    mail = smtplib.SMTP(usr_smtp_server, 25)
    header = 'To: ' + usr_to + '\n' + 'From: ' + usr_from + '\n' + 'Subject: ' + usr_subject + '\n'
    msg = header + '\n' + usr_msg + '\n'
    mail.sendmail(usr_from, usr_to, msg)
    mail.close()

#checks the exclusion list and the threshold of the disk. If there is low space it writes to the msg variable
my_disks = get_filesystem()
for d in my_disks:
    if d[0] in exclusion:
        continue
    if low_disk(d) == True:
        msg += 'Filesystem: ' + str(d[0]) + ' is low on freespace: ' + str(d[4]) + '% in use.\n\n'

#if the msg variable has data an email is sent
if msg != '':
    msg = 'Hostname: ' + get_hostname() + 'The current alert threshold is set at ' + str(percent_threshold) + '% used space.\n\n' + msg
    send_mail(msg)
