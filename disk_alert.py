#! /usr/bin/python

#use cron to schedule an instance of this script. If there are no alerts the script ends until the new cron job. If
#the warning or error thresholds are exceeded the warning_sleep_time_second and/or error_sleep_time_second variables
#tell the script the amount of time to re-run checks. It will continue to run until the run_time_seconds variable has
#been exceeded. At this time the script terminates until cron re-spawns the script.
#recommended settings:
#crontab -e
#0 12 * * * /script
#warning_sleep_time_second = 21600
#error_sleep_time_second = 3600
#run_time_second = 84600

import smtplib, os, time

#if used space is >= these variables an alert will be sent. Warning always needs to be <= error.
warning_percent_threshold = 90
error_percent_threshold = 95
#empty message
msg = ''
#add the filesystem name to the exclusion list if you need it ignored
exclusion = ['/dev/sr0']
#warning flag to send alert
warning = False
#amount of time between warning emails
warning_sleep_time_second = 21600
#error flag to send alert
error = False
#amount of time between error alerts
error_sleep_time_second = 3600
#start time of the script
start_time = time.time()
#automatically kills the script after this many seconds. This allows the script to die and cron to spawn a new instance.
run_time_second = 83700

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

def low_disk_error(disk_info):
    #determines if the used disk space is higher than the error and warning thresholds and returns true or false
    if (disk_info[4] > warning_percent_threshold) and (disk_info[4] >= error_percent_threshold):
        return True
    else:
        return False

def low_disk_warning(disk_info):
    #determines if the used disk space is higher than the warning threshold and lower than the error threshold
    #returns true or false
    if (disk_info[4] >= warning_percent_threshold) and (disk_info[4] < error_percent_threshold):
        return True
    else:
        return False

def send_mail(usr_msg):
    #creates and sends email through the markit smtp server
    usr_smtp_server = 'ussmtp.markit.partners' #'appsmtp1.markit.partners'
    usr_to = 'MK-GTSSolutionsEngineeringVirtualization@markit.com'
    usr_from = 'vcs-lon6@markit.com'
    if error:
        usr_subject = 'ERROR :: LOW DISK SPACE ALERT ON ' + str(get_hostname()).upper()
    elif warning:
        usr_subject = 'WARNING :: LOW DISK SPACE ALERT ON ' + str(get_hostname()).upper()
    else:
        usr_subject = 'INFORMATION :: DISK_ALERT.PY SCRIPT ON ' + str(get_hostname()).upper()
    mail = smtplib.SMTP(usr_smtp_server, 25)
    header = 'To: ' + usr_to + '\n' + 'From: ' + usr_from + '\n' + 'Subject: ' + usr_subject + '\n'
    msg = header + '\n' + usr_msg + '\n'
    mail.sendmail(usr_from, usr_to, msg)
    mail.close()

def check():
    #checks the exclusion list and the threshold of the disk. If there is low space it writes to the msg variable
    #if there is a low disk warning or error the flag is changed to trigger an alert
    global warning, error, msg
    my_disks = get_filesystem()
    for d in my_disks:
        if d[0] in exclusion:
            continue
        if low_disk_warning(d) == True:
            msg += 'Filesystem: ' + str(d[0]) + ' is low on freespace: ' + str(d[4]) + '% in use.\n\n'
            warning = True
        if low_disk_error(d) == True:
            msg += 'Filesystem: ' + str(d[0]) + ' is low on freespace: ' + str(d[4]) + '% in use.\n\n'
            error = True
    if (start_time - time.time()) * -1 > run_time_second:
        warning = False
        error = False

#main
#send_mail('The cron has spawned v2!')
check()

while warning == True or error == True:
#while the warning or error flags are true and email is triggered. The script sleeps based on the alert type and runs
#a new check when it wakes up. Once there are no alerts the script ends until cron spawns a new instance.
    if error == True:
        msg = 'Hostname: ' + get_hostname() + 'The current ERROR alert threshold is set at ' + str(error_percent_threshold) + '% used space.\n\n' + msg
        send_mail(msg)
        time.sleep(error_sleep_time_second)
        error = False
        msg = ''
        check()
        continue
    if warning == True:
        msg = 'Hostname: ' + get_hostname() + 'The current WARNING alert threshold is set at ' + str(warning_percent_threshold) + '% used space.\n\n' + msg
        send_mail(msg)
        time.sleep(warning_sleep_time_second)
        warning = False
        msg = ''
        check()
        continue

#send_mail('The cron has died v2!')
