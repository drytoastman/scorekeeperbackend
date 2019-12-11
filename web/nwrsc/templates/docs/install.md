# Installation

## Requirements
1. A Docker environment for your operating system, some common installation instructions are:
    - [OS X](https://docs.docker.com/docker-for-mac/install/)
    - [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
    - [Windows 10 Home](https://docs.docker.com/toolbox/toolbox_install_windows)
    - [Windows 10 Pro](https://docs.docker.com/docker-for-windows/)

## Installing
1. Verify that the above requirements for Docker on your OS distribution (a system install of Java is no longer required)

1. Download the latest scorekeeper zip from <https://github.com/drytoastman/scorekeeperfrontend/releases> for your OS and extract to a chosen directory.

1. You run Scorekeeper using **StartScorekeeper** or **StartScorekeeper.bat** depending on your OS

1. The first time you download a new version, you should run **StartScorekeeper**
   while connected to the Internet so that the backend is properly downloaded
   and a database is setup.

1. If you have never run Scorekeeper on the target machine, you should also run
   either **LoadCerts** or **LoadCerts.bat**.  You will be asked for the
   certificates file,  select the **certs.tgz** provided by your administrator.

   <span style='color:red'>
   Without this step, you cannot sync with scorekeeper.wwscc.org or other laptops.
   </span>

1. For non-Linux installs you **may** need to open incoming firewall ports depending on your own system:
    * **TCP:80**    for the local web server (results, etc)    
    * **TCP:54329** for syncing with other nearby machines
    * **TCP:54328** for most network timer connections (i.e. ProSolo Timer)
    * **UDP:53**    standard unicast dns for onsite resolving of "de" and "reg" to a Scorekeeper laptop IP
    * **UDP:5353**  standard multicast dns for onsite resolving of "de" and "reg" to a Scorekeeper laptop IP
    * **UDP:5454**  for discovering nearby machines or network timers

    * For windows machines, you can run **rules.bat** as **Administrator** to insert theses rules and
      turn off the IIS and InternetConnectionSharing services that get in the way.
