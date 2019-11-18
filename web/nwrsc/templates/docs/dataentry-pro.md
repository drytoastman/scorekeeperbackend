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

2. **Sort** - this is the order of grid entrants, either number or position.  **Number** ordering is used in the morning, **Position** ordering is used in
the afternoon.

3. **Overwrite Current Order** - the default is off which means we are appending a new chunk of entries to the runorder as grid brings us new groups
of cards.  If this is checked, the current runorder will be cleared before adding the selected entries.  This can be used when loading the first set of
cars in the afternoon.

4. **Load To** - if each data entry person is loading the grid individually, select **This Course** and it will only load entrants to the current course.
If **Both Courses** is selected, it will load the grid to both courses at the same time.  The other data entry will seen their screen update after a sync
occurs.  Use **Both Courses** only if the other data entry person is aware you are doing this.

You can see in the image that the top section of entries are greyed out.  This
is because they are already in a runorder for the current event. The rest of
the entries are not in the runorder and can be selected and added.  You can
still selected greyed out entries, but they will be ignored. There are also two
tables of entries, the first/single drivers and then the dual drivers.  The
current implementation assumes that the dual drivers you select will come after
the first/single drivers.

Upon clicking **OK**, the left course (**1**) will have all of the left drivers
appended to the runorder followed by all of the right drivers, while the right
course (**2**) will have the opposite ordering, matching the order in which
they should appear to each side.  This process can be repeated for each new
grouping of cars to be released from grid.


## Group Markings and Next Cell

Data entry during a Pro will attempt to be smarter amount selecting the next
time cell.  It will look at the runorder of both courses and try and determine
where the groups are divided up.  These will be marked with a green horizontal
line as seen below:

![GroupingLine](images/prodivider.png)

On 1st, 3rd and 5th runs, if it hits one of these boundaries, it will wrap back
up to the top of the subgrouping, otherwise it will continue down as per
normal.  As always, the data entry person is responsible for verifying that
they are commiting the time to the correct entrant.
