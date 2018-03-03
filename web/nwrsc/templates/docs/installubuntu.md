# Installing on Ubuntu

1. Download the latest ubuntusetup.sh script from <https://github.com/drytoastman/scorekeeperfrontend/releases> 

2. Run the script with:

    `sudo bash ./ubuntusetup-(VER).sh`

3. The installer will:
    * add the docker repo and gpg key
    * install docker-ce, openjdk8 and openjfx
    * add the current user to the docker group so the frontend can start/stop containers
        * See security implications at <https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user>
    * download the latest jar file to the current working directory
    * prememptively download the backend container images

4. Run the following to start scorekeeper:

    `java -jar scorekeeper-(VER).jar`

