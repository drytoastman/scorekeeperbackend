# Non Database Installs

There are a couple applications (**BWTimer**, **ProTimer**) that do not require a database to run.
If these are the only applications are to be run on a machine, you can ignore the standard Docker
installation and only install Java 8.  Next, download the latest jar from the
[releases page](https://github.com/drytoastman/scorekeeperfrontend/releases) and create shortcuts
or other such methods to invoke the jarfile as so:

  **ProTimer**: `java -cp <jarfile> org.wwscc.protimer.ProSoloInterface`

  **BWTimer**:  `java -cp <jarfile> org.wwscc.bwtimer.Timer`

