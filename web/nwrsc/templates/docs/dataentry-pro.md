# Data Entry for a ProSolo

All of the normal functions from a regular event apply to the prosolo.  See the [main DataEntry](dataentry.md) page for those instructions. The
following are instruction specific to a ProSolo event.

---

## Loading Run Order from Grid Report

It is possible to load the run order from the official grid report in sections.  As we don't always know where the groups will be broken up, this
piece by piece loading is necessary.  The dialog to do this can be found under **ProSolo** menu as **RunOrder From Grid** or by using **Ctl+R**.

![RunOrderFromGridDialog](images/loadrunorder.gif)

At the top are several options:

1. **Grouping** - this is the grid grouping from the admin page.  Generally just group 1 and group 2.  These may or may not line up with the actual
rungoups they end up running in.  i.e. grouping 2 may run first based on the coin flip

2. **Order** - this is the order of grid entrants, either number or position.  Number ordering is used in the morning, Position ordering is used in
the afternoon though **Reordering Run Order by Position** below is probably the better solution for the afternoon.

3. **Overwrite Current Order** - the default is off which means we are appending a new chunk of entries to the runorder as grid brings us new groups
of cards.  If this is checked, the current runorder will be deleted before adding the selected entries.

You can see in the image that the top section of entries are greyed out.  This is becuase they are already in a runorder for the current event. The
rest of the entries are not in the runorder and can be selected and added.  You can still selected greyed out entries, but they will be ignored. There
are also two tables of entries, the first/single drivers and then the dual drivers.  The current implementation assumes that the dual drivers you
select will come after the first/single drivers.

Upon clicking **OK**, the left course (1) will have all of the left drivers appended to the runorder followed by all of the right drivers, while
the right course (2) will have the opposite ordering, matching the order in which they should appear to each side.  This process can be repeated for
each new grouping of cars to be released from grid.

*<span style='color:red'>Note:  This loads cars on both courses at the same time so only 1 data entry person should perform this action.  The other
dataentry will refresh its screen automatically after a sync occurs.</span>*


## Reordering Run Order by Position

If the grouping of cars released by grid will remain the same in the afternoon, rather than start with a fresh grid and following the process above,
you can run a single command to reorder all the entrants in the current run group.  Select **Reorder By Net** from the **ProSolo** menu.

The current run order for for course 1 and 2 will be scanned for all the spots and which class they are assigned to.  These spots are then assigned
the entrants from each class based on their finishing position with accouting for second drivers.  This will only be done for the current run group.

*<span style='color:red'>Note:  This updates cars on both courses at the same time so only 1 data entry person should perform this action.  The other
dataentry will refresh its screen automatically after a sync occurs.</span>*


