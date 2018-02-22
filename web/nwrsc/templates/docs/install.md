# Manual Installation

## Requirements
1. A Docker environment, the Community Edition install info is at <https://docs.docker.com/engine/installation/>
1. Java 8 JRE (including JavaFX) or above, see your OS info for details or <http://www.oracle.com/technetwork/java/javase/downloads/index.html>

## Installing
1. Verify that the above requirements for Docker and Java based on your OS distribution

1. Download the latest Scorekeeper jar from <https://github.com/drytoastman/scorekeeperfrontend/releases> to your computer

1. Create a method to run the jarfile as so:

    ```java -jar <jarfile>```

1. The first time you run a new version it will download the necessary docker images, showing the following status as it does so:
    * Init scweb
    * Init scsync
    * Init scdb

1. Eventually the Backend status should report as "Running".  Everything should be ready to go.

1. For non-Linux installs you may need to open incoming firewall ports depending on use:
    * **TCP:80**    for the local web server (results, etc)    
    * **UDP:5454**  for discovering nearby machines or network timers
    * **TCP:54329** for syncing with other nearby machines
    * **TCP:54328** for most network timer connections (i.e. ProSolo Timer)

