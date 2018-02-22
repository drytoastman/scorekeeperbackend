# Notes For General Use

1. Starting and stopping the TrayApplication should be quick as the containers are quick to start and stop
1. The only long delay is on Windows when restarting the virtual machine after a reboot or logoff

    ![ContextMenu](images/startingvm.png)

3. All Scorekeeper applications should be started from the tray menu or status window menu
3. If the TrayApplication isn't running, the database is 99% most likely not running so applications will not work anyhow
3. For consistency, each Scorekeeper version is assigned its own storage 'folder', therefore
    * Upgrading versions or changing users will use different data 'folders'
    * You can import old data from a previous 'folder' if we need to

