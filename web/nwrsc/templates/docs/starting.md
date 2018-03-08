# Starting the System

Starting and stopping the ScorekeeperSystem should be quick as the containers are quick to start and stop.
The only long delay is on Windows or OS X when restarting the virtual machine after a reboot or logoff.

## Status
The boxes at the top of the stastus window indicate the status of the backend.  Green is good, red means
something is wrong.  The machine box lists the status of the docker-machine virtual machine.  The backend
status lists the status of the database, web server and sync server. 

   ![ContextMenu](images/startingvm.png)

## Launching Applications

All Scorekeeper applications should be started from the tray menu or status window.  If the system 
isn't running, the database is 99% most likely not running so applications will not work anyhow.

## Getting the Status Window Back
When main scorekeeper application is run, a status window will appear.  On system with a cone tray icon, you can reopen
the window by selecting **Status Window** from the tray menu.

![ContextMenu](images/syncmenu.png)

