# Status and Synchronization

## With scorekeeper.wwscc.org

### Downloading a New Series
1. Click **Download New Series From ...** and then select **scorekeeper.wwscc.org**.  As you can see, you can also download
   a new series from a local machine that has already downloaded the series earlier.
2. Remote series that are not present on the machine will be loaded, after which you can select one
3. Enter the password for the series and click **Verify Password**
4. If the password is correct, the button will change to **Download**, otherwise try the password again
5. Click **Download** and let it finish

    ![DownloadFrom](images/downloadnew.gif)

### Syncing A Series
1. Click **Sync With ..** and then select **scorekeeper.wwscc.org**.  This is very similar to the sync all active button but
   you can select a non-active remote host.  In this case, there are no local servers we are in contact with, so only
   scorekeeper.wwscc.org shows up.

    ![SyncWith](images/sync.gif)


## With other computers on a local network

These should be discovered automatically and they will show up in the Active table.  By default, we check sync status with
other local machine every 60 seconds.  If the computer was just connected to the network and you don't want to wait, you
can click **Sync All Active Now** which tells the sync server to schedule a sync check now.

## Active/Inactive
The tables in the window contain the lists of active hosts and inactive hosts. The first host in the active
table is always the local machine.  Active hosts will include those discovered locally that we are still
in contact with and any remote hosts that are processing a sync request from the user.  Inactive hosts include
remote servers that we are finished syncing with or local servers that we cannot connect to anymore (off network).

Any red boxes in the status table indicate something of potential interest.  A red time value indicates that the
time is far enough in the past that we may no longer be in sync but we do not know for sure.  A red value in one
of the series columns indicates that an error occured or that the remote version of the series is in a different
state from the local machine.  You can hover the mouse over the cell to potentially sure more information about
the error.  The seemingly random data under the series columns are actually part of a hash calculation of the
series contents.  If they are the same, the data is in sync.

When actively syncing a series, you will see the sync icon ![syncicon](images/syncing.png) along with some status text.


