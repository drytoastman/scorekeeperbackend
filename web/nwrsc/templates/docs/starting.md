# Starting the System

Starting and stopping the Scorekeeper System should be relatively quick as the containers are quick to start and stop.
The only long delay is on Windows or OS X when restarting the virtual machine after a reboot or logoff or when initializing
a new database.

## Status
The boxes at the top of the stastus window indicate the status of the backend.  Green is good, red means
something is wrong.  The machine box lists the status of the docker-machine virtual machine.  The backend
status lists the status of the database, web server and sync server. 

   ![Starting System](images/startup.gif)

## Launching Applications

All Scorekeeper applications should be started from the status window via the Applications menu.  If the system 
isn't running, the database is 99% most likely not running so applications will not work anyhow.

