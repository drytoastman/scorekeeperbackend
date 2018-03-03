# Non Database Installs

There is one application, **ProTimer**, that does not require a database to run.
If this is the only application to be run on a machine, you can ignore the standard Docker
installation and only install Java 8.  Next, download the latest jar from the
[releases page](https://github.com/drytoastman/scorekeeperfrontend/releases) and create a shortcut
or other such method to invoke the jarfile as so:

    java -cp <jarfile> org.wwscc.protimer.ProSoloInterface

