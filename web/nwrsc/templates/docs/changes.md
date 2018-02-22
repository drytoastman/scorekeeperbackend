# Changes from Version 1

1. **Each machine uses a real database server (Postgresql)** that contains all the downloaded series data rather than
   individual SQLite files.

1. **All results and meta calculations take place in one location**.  Even the data entry announcer panel will pull its
   data from the backend as a web page.  No more repeated logic in different places.

1. **All changes and timer data are logged to the database**. These all include a timestamp so recreating the sequence
   of events that occured to get to a particular state should be possible.

1. **Web sites are based off of Flask/Jinja** rather than the old Pylons/Mako stuff.

1. **The drivers table is shared between all series** so everyone has a single profile that is shared across all
   series.  For this reason, deleting drivers is best left to the drivers merging tool on the main server.  There
   are other controls that should help eliminate the duplicate driver entry problems.

1. **We use UUIDs now and every machine acts as its own master** so synchronizing between machines can happen at anytime.
   There is no more master-slave relationship or changesets when syncing.  Sync determines changes to the data by
   comparing sets of primary keys and modification times.  If both machines have modififed an entry, the most
   recent time wins.

1. **The database, web server and sync server all run inside docker containers** to maintain the same behavior in
   all environments.

1. **The backend monitor stays active as a system tray icon** that can launch the status window for the backend
   as well launch the Java applications.

1. **A new HTML template for printing timing cards is available**.  The old PDF cards still exist still but are effectively
   deprecated.  Better browser and CSS improvements since the old days allow for printing cards from a HTML template
   that is much easier to modify as the user sees fit.   It is also more secure that executing user python code.

1. **User customizations are limited to results CSS and the header field**.  Noone used the complete results templates and
   maintaing those between versions was a pain.

1. **The old dataentry quick entry has been changed**.  All driver, car and event ids are now UUIDs which are hard to type.
   Instead, the lower portion of the time value of the UUID is turned into an integer and printed on the timing cards. These
   are still rather long so a list of registered users is shown that gets smaller as you type digits.  Once it reduces to one,
   you can hit enter to add the entrant rather than typing the whole number.

1. **Online payments are supported** through authorizing a Square application and/or the new Paypal REST API.


