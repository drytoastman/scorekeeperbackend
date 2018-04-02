# Backups

For consistency, each Scorekeeper major.minor version is assigned its own storage folder, therefore upgrading
versions or changing users will use different data folders.

    2.1.0 and 2.1.1 would use one folder
    2.2.0 would use a different folder

## Local Backups

### Automatic 
Every time the scorekeeper backend is shutdown normally using the Shutdown command, a backup of the
local database is saved in $HOME/scorekeeper/$VERSION/backup/ with a date and schema information in the name.

### Manual
You can also manually make a backup from the Scorekeeper Status Window using File &rarr; Backup Database.

### Restoring
Either of the above backups can be restored from the Scorekeeper Status Window using File &rarr; Import Backup Data.

## Online Backups

The primary Scorekeeper server database is backed up on a daily basis to a offsite server.


# Collecting Debug Data

The status Window contains a menu **Debug**.  Under this is an item called **Collect Debug Data**.  This will
collect all the frontend logs, backend logs and the database data itself and put it into a zipfile that can be
sent to me for figuring out what broke.

## Setting log level

There is also a menu item for setting the debug level.  This can be increased to maximum when recreating an
issues.  You must restart the backend for it to take effect is all places.  Once restarted, you can recreate
the issues and then collect debug data again.

