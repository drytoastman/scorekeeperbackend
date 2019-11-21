# Manual Installation

## Requirements
1. A Docker environment for your operating system, some common installation instructions are:
    - [OS X](https://docs.docker.com/docker-for-mac/install/)
    - [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
    - [Windows 10 Home](https://docs.docker.com/toolbox/toolbox_install_windows)
    - [Windows 10 Pro](https://docs.docker.com/docker-for-windows/)

## Installing
1. Verify that the above requirements for Docker on your OS distribution (a system install of Java is no longer required)

1. Download the latest scorekeeper zip from <https://github.com/drytoastman/scorekeeperfrontend/releases> for your OS and extract to a chosen directory.

1. You run Scorekeeper from either **(DIR)/bin/ScorekeeperFrontend** or **(DIR)/bin/ScorekeeperFrontend.bat** depending on your OS

1. As a one time only step, run the above command with the argument **dockerprepare** (i.e. *bin/ScorekeeperFrontend dockerprepare* )

    * it will first ask you if you **want to install new certificates**, click yes if you haven't done this yet and then select the **certs.tgz** file provided by your administrator
    * it will then start Scorekeeper to make sure the backend is downloaded and a database is initialized

1. For non-Linux installs you may need to open incoming firewall ports depending on use:
    * **TCP:80**    for the local web server (results, etc)    
    * **UDP:5454**  for discovering nearby machines or network timers
    * **TCP:54329** for syncing with other nearby machines
    * **TCP:54328** for most network timer connections (i.e. ProSolo Timer)
