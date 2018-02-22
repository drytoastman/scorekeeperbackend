# Backups

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

