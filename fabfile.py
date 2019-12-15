###############################################################################
# Author: Brandon Ekins, Cameron Cummings                                     #
# Date: 23 May 2019                                                           #
# Version: 2.0.7                                                              #
#                                                                             #
# This program is for managing IP blacklists and installed packages on remote #
# Debian machines. It can:                                                    #
#   - Add a list of IP addresses to an ipset blacknet list                    #
#   - Get a list of available package upgrades and save to a local file       #
#   - Install all available package upgrades                                  #
#   - Install a package using apt                                             #
#   - Remove unused packages                                                  #
#   - Reboot servers                                                          #
###############################################################################

from fabric.api import *
import getpass
env.parallel = False
from cStringIO import StringIO
import sys
import socket
import time
# global constants
PROXYIP = socket.gethostbyname("lsweblsb.byu.edu")
BLOCKEDFILE = ""

###############################################################################
# Set up the necessary global conditions, like login username and passeword.  #
# This is done here so that these questions are not repeated for each host.   #
###############################################################################
if len(sys.argv) == 2 : # Added this check so that it only works if you have a single arg. Change if more then 1 arg is needed later
    if sys.argv[1] == "Deploy" or sys.argv[1] == "updateServers" or sys.argv[1] == "rebootServers" or sys.argv[1] == "autoremove" or sys.argv[1] == "listUpgrades" or "install" in sys.argv[1]:
        hostFileInput = raw_input("Host list: ")
        p = open(hostFileInput)
        env.hosts = [i[:-1] for i in p.readlines()]
        env.warn_only = True
        env.skip_bad_hosts = True
        env.user = raw_input("Login username: ")
        env.password = getpass.getpass("Enter %s's password: " %env.user)
        if sys.argv[1] == "Deploy":
            BLOCKEDFILE = raw_input("Input blacklist filename: ")

    elif (sys.argv[1] == "getList" or sys.argv[1] == "addNewServer"):
        env.hosts = raw_input("Host name: ")
        env.password = getpass.getpass()
        env.warn_only = True
        env.skip_bad_hosts = True
###############################################################################
# Deploy blacklist from a local file to a list of remote servers. The list of #
# IP addresses in the blacklist will be merged with the blacklist already on  #
# the remote server.                                                          #
###############################################################################
def Deploy():
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True #does not stop if it comes across an error
    ):
        print("Executing script on %(host)s" % env)#says what host the script is running on
        listexist = sudo("ipset list | grep blacknet")
        if listexist == "": #if blacknet list does not exist, create it
            sudo("ipset create blacknet hash:net family inet hashsize 4096 maxelem 65536")
        for line in open(BLOCKEDFILE):#iterates through the file on the localhost
            line = line.replace("\n","")
            if line[-3:] != "/24": # Check if this line has bee properly formatted
                line += "/24" # if not, format it
            runval = "ipset add blacknet " + line #adds files to blacklist on host
            sudo(runval)
        print("Done updating ipset on %(host)s" % env)
        #Tests if ipset.conf location exists.
        value = sudo("ls /etc/ipset")
        if "No such file or directory" in value:
            sudo("mkdir /etc/ipset && touch /etc/ipset/ipset.conf")
        sudo("ipset save > /etc/ipset/ipset.conf")#saves blacklist on the host

###############################################################################
# DEPRECATED - This operation happens as part of Deploy now                   #
# Append /24 to the end of all IP addresses in a blacklist file. This will    #
# block all IP addresses in the subnet.                                       #
###############################################################################
def formatList():
    BLOCKEDFILE = raw_input("Input file name: ")
    outFile = raw_input("Output file name: ")
    newFile = ""
    for line in open(BLOCKEDFILE):
        newFile += line[:-1]+"/24" + "\n"
    f = open(outFile,'w')
    f.write(newFile)
    f.close()

###############################################################################
# DEPRECATED - Unnecessary                                                    #
# Remove the /24 from each IP address in a blacklist file.                    #
###############################################################################
def unformatList():
    BLOCKEDFILE = raw_input("Input file name: ")
    outFile = raw_input("Output file name: ")
    newFile = ""
    for line in open(BLOCKEDFILE):
        newFile += line[:-4]+ "\n"
    f = open(outFile, 'w')
    f.write(newFile)
    f.close()

###############################################################################
# Grab the ipset list from remote server and write it to a file.              #
###############################################################################
def getList():
    outFile = raw_input("Output file name: ")
    list = run("ipset list")#this pulls the file from the remote server
    i = 0
    hs = open(outFile,"w")
    s = list.split("\n")
    for line in s:
        if i > 6:#this removes the header
            hs.write(line)
        i += 1
    hs.close()

###############################################################################
# Format a list of items to remove all carriage return and newline chars,     #
# then return the formatted list. Can also take string variables with         #
# multiple lines, in which case a list will be created by splitting at        #
# newlines. The newly created list will then be formatted.                    #
###############################################################################
def cleanList(ufList):
    if str(type(ufList)) == "<type \'str\'>": #convert to list
        ufList = ufList.split("\n")
    fList = []
    for item in ufList: #remove carriage return and newline
        item = item.replace('\r', '')
        item = item.replace('\n', '')
        fList.append(item)
    return fList

###############################################################################
# Install a package on a Debian machine using apt.                            #
# Syntax: fab install:<packageName>                                           #
###############################################################################
def install(package = ""):
    if package == "":
        print "No package name set. You can set one here, but it will ask you for the name for each host. The best way to set the package name is to run \'fab install:<packageName>\'"
    while package == "":
        package = raw_input("Please enter a package name: ")
    result = sudo("apt update && apt install -y %s" %package)
    if result.failed:
        sudo("apt-get update && apt-get install -y %s" %package)

###############################################################################
# Get a list of all available upgrades on a list of remote Debian servers and #
# save the output locally in a file called UpgradesAvailable.txt. Timestamps  #
# are used to ensure that the information is current, and the program will    #
# overwrite any output file that is more than TIMEOUT seconds old. This       #
# should allow it enough time to get the information from all the hosts and   #
# write them to the file while at the same time preventing the file from      #
# containing outdated information. The specific length of time can be changed #
# by changing the value of the variable TIMEOUT. As an extra precaution, a    #
# line of '*' characters will be added after all hosts have been checked.     #
###############################################################################
def listUpgrades():
    with hide('stdout'):
        currentHost = "%(host)s" % env
        upgradeTime = time.time()
        output = str(upgradeTime) + "\nHostname: " + currentHost + "\n"
        outFile = "UpgradesAvailable.txt"
        currHostIP = ""
        try:
            currHostIP = socket.gethostbyname(currentHost)
        except:
            output += "\nInvalid hostname: %s\n" % currentHost
        if currHostIP == PROXYIP and currentHost != "lsweblsb.byu.edu":
            output += "\nThis connection has been redirected to the proxy. Please check the hostname.\n"
        elif currHostIP != "":
            try:
                output += "IP address: " + currHostIP + "\n"
                osvers = run("lsb_release -a | grep \"Description:\"")
                osvers = osvers.split("\n")
                osvers = osvers[len(osvers)-1]
                output += osvers + '\n'
                kernel = run("uname -r")
                output += "Kernel version: " + kernel + "\n\n"
                update = sudo("apt update")
                if "Failed" in update:
                    error = "There is something wrong on " + currentHost + ". Skipping..."
                    print error
                    output += error + "\n"
                else:
                    tempFilename = "/tmp/upgrades"+str(upgradeTime)+".txt"
                    upgradesString = sudo("apt list --upgradable > " + tempFilename + " && cat " + tempFilename + " && rm " + tempFilename)
                    upgradesList = upgradesString.split("\n")
                    upgradesList = cleanList(upgradesList)
                    upgradesCount = 0
                    for item in upgradesList:
                        if "upgradable" in item:
                            output += item + '\n'
                            upgradesCount += 1
                    if upgradesCount == 0:
                        output += "<none>\n"
            except Exception, e:
                output += "\n" + str(e) + "\n"
        output += '\n---------------------------------\n\n'
        if env.hosts.index(currentHost) == len(env.hosts)-1:
            output += "**************************************************\n"

        #Attempt to open the previously created outFile and extract its first timestamp
        try:
            file = open(outFile, 'r')
            timestamp = int((file.readline().split("."))[0])
            file.close()
        except IOError, Argument:
            timestamp = time.time()

        #write output to file, following the restriction explained above
        TIMEOUT = 500
        if time.time() - timestamp <= TIMEOUT:
            file = open(outFile, 'a')
        else:
            file = open(outFile, 'w')
        file.write(output)
        file.close()
###############################################################################
# Install all available package upgrades.                                     #
###############################################################################
def updateServers():
    result = sudo("apt upgrade -y")
    if result.failed:
        sudo("apt-get upgrade -y")

###############################################################################
# Remove all packages that are no longer needed, as determined by apt.        #
###############################################################################
def autoremove():
    result = sudo("apt autoremove -y")
    if result.failed:
        sudo("apt-get autoremove -y")

###############################################################################
# Reboot all servers in the list. Sometimes hangs for a bit as the reboot     #
# interrupts the connection. If it hangs, it can sometimes be "nudged" with a #
# keyboard input.                                                             #
###############################################################################
def rebootServers():
    sudo("reboot")

###############################################################################
# This replaces all the mirrors with the ones given in a text file            #
#                                                                             #
###############################################################################
def changeMirrors():
   pass
