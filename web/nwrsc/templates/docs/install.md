# Install/First Use

## Requirements
1. A Docker environment
    * implies a 64bit OS and a processsor that support virtualization (most recent laptops do)
1. Java 8 (including JavaFX) or above

## Installing on Windows (Docker-Toolbox + Java 8)
1. Download the latest ScorekeeperSetup installer from <https://github.com/drytoastman/scorekeeperfrontend/releases> 
2. Windows Pro users will get a reminder that Hyper-V must disabled to use Docker-Toolbox (based on Oracle VirtualBox)
3. The installer will perform all setup and put an entry in the startup folder and on the desktop
    * The installer may foward you to websites to install Java 8 and/or Docker-Toolbox if they are not present already
    * This version has to run a virtual machine which takes about 60 seconds to startup the first time after logging in

## Installing on 64bit Linux or Mac OS X
There is no installer at this point so you need to do a few things manually

1. Verify that the above requirements for Docker and Java based on your OS distribution
    * For Docker see the Community Edition at <https://docs.docker.com/engine/installation/>
1. Download the latest Scorekeeper jar from <https://github.com/drytoastman/scorekeeperfrontend/releases> to your computer
1. Create a method to run 

    ```java -jar <jarfile>```

1. The first time you run a new version it will download the necessary docker images, showing the following status as it does so:
    * Init scweb
    * Init scsync
    * Init scdb
1. Eventually the Backend status should report as "Running".  Everything should be ready to go.
1. You may need to open incoming firewall ports depending on use:
    * **TCP:80**    for the local web server (results, etc)    
    * **UDP:5454**  for discovering nearby machines or network timers
    * **TCP:54329** for syncing with other nearby machines
    * **TCP:54328** for most network timer connections
    

## Notes on Application Use

1. Starting and stopping the TrayApplication should be quick as the containers are quick to start and stop
1. The only long delay is on Windows when restarting the virtual machine after a reboot or logoff

    ![ContextMenu](images/startingvm.png)

3. All Scorekeeper applications should be started from the tray menu or status window menu
3. If the TrayApplication isn't running, the database is 99% most likely not running so applications will not work anyhow
3. For consistency, each Scorekeeper version is assigned its own storage 'folder', therefore
    * Upgrading versions or changing users will use different data 'folders'
    * You can import old data from a previous 'folder' if we need to

## Collecting Debug Data

The status Window contains a menu item "Debug Collection".  This will collect all the frontend logs, backend logs and the database data itself and put it into a zipfile
that can be sent to me for figuring out what broke.


