# Installing on Windows

*Make sure Docker is installed and works, either [Docker Toolbox](https://docs.docker.com/toolbox/toolbox_install_windows) (Home) or [Docker Desktop](https://docs.docker.com/docker-for-windows/) (Pro) depending on your version of Windows*

1. Download and run the latest ScorekeeperSetup.exe installer from <https://github.com/drytoastman/scorekeeperfrontend/releases> while connected to the Internet

2. The installer will perform all setup and put an entry in the startup folder and on the desktop
    * It now installs its own embedded version of Java so you no longer need a system version of Java installed

    * It will attempt to disable some conflicting Windows services:
        - w3svc (web server that also binds to port 80)
        - SharedAccess (Interet Connection Shared that also binds to port 53)
    * It will open ports in the firewall:
        - 53/5353 (onsite DNS)
        - 80 (onsite web results, announcer page, etc)
        - 5454 (scorekeeper peer discovery)
        - 54328 (network timer port, Prosolo)
        - 54329 (scorekeeper sync port to postgres)

3. At the last step of installation:
    1. You will be asked if you want to install new certificates. If you have never done this before on this machine, click yes and select the certs.tgz file provided by your administrator
    2. Scorekeeper will be started to make sure the backend is downloaded and a database is initialized

4. If your need to rerun **#3** for any reason, there will be a shortcut install in the start menu call **Scorekeeper Prepare** that you can run.
