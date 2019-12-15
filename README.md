# General Instructions
At the begining of each job make sure you have a file(inventory) with a list of hosts you want to target (name this file "hosts").

Then edit the "hosts" field to the group of hosts you want to run the script against by typing "all", "[groupName]", or "IndividualRemoteHostName". (This is done inside the playbook YAML file you will run, if you are running multiple YAML files, then do so in each individual file)

Then run the ansible-playbook. (if needed you can add --ask-become-pass and/or --ask-pass)

## Commands:

To use a yaml playbook the command is: 

ansible-playbook -K {playbook-name}.yaml --ask-become-pass --ask-pass

*K must be capitalized*
## Install
To run this playbook, make sure you edit the file by adding the name of the packages you want to update. Do this under apt -> name with "- " in front. Each package in its seperate line directly under the previous one(if there are multiple).
### Deploy
This playbook will prompt you to input the path to the BLOCKLIST file is on your computer.
Deploy blacklist from a local file to a list of remote servers. The list of IP addresses in the blacklist will be merged with the blacklist already on the remote server. Append /24 to the end of all IP addresse in a blacklist file. This will block all IP addresses in the subnet.
### getlist
This playbook will prompt you to input the path to where you want the file to be created to print the ipset list to.
Grab the ipset list from remote server and write it to a file.
### listUpgrades
Get a list of all available upgrades on a list of remote Debian servers and save the output locally in a file called UpgradesAvailable.txt. Timestamps are used to ensure that the information is current, and the program will overwrite any output file that is more than TIMEOUT seconds old. This  should allow it enough time to get the information from all the hosts and write them to the file while at the same time preventing the file from containing outdated information. The specific length of time can be changed by changing the value of the variable TIMEOUT. As an extra precaution, a line of '*' characters will be added after all hosts have been checked.
### updateServer
Install all available package upgrades.
### autoRemove
Remove all packages that are no longer needed, as determined by apt.
### rebootServers
Reboot all servers in the list. Sometimes hangs for a bit as the reboot interrupts the connection. If it hangs, it can sometimes be "nudged" with a keyboard input.

### ansible.cfg
This cotains the configurations for ansible to reach the remote servers
