
# Java FX Challenge GUI

The new challenge GUI is split into two halfs.  The top half contains staged
entrants for the timer.  The bottom half shows the challenge bracket.

## Creating a New Challenge

Verify that the correct event is selected in the Event pull down.  From the
**Challenge** menu, select **New Challenge**.

![ChallengeMenu](images/fxcmenu.png)

A new dialog will appear where you can enter the challenge name as well as the
bracket size (8,16,32,64)

![NewDialog](images/fxcnewdialog.png)

After selecting **OK**, a new blank bracket will be shown

![NewWindow](images/fxcnewwindow.png)


## Loading the Initial Rounds

To load entrants, from the **Challenge** menu, select **Load Entrants**.  The
load entrants dialog will appear.  You can check/uncheck the **Ladies** and
**Open** classes checkboxes to show/hide those classes.  You can check **Bonus
Dialins** if you want to use bonus dialins instead of class dialins.

Using the shift or Ctrl keys and the mouse, select the desired entrant for the
challenge.  You must select between N/2-1 and N entrants before the OK button
will be active.  i.e. for a 16 entrant challenge, you must select between 9 and
16 entrants.

![LoadEntrants](images/fxcloadentrants.png)

Once you are done, click OK, the bracket display in the lower half of the
screen will update with the entrants.  They are ordered by net finishing time.

![BracketDisplay](images/fxcbracketdisplay.png)


## Staging Entrants

For dialins to get sent to the timer or for runs from the timer to be recorded,
they entrants must be staged in the table in the upper half.  To stage a new
pair, **LEFT CLICK** on the round you want to stage to bring up the menu for that
round.

![BracketMenu](images/fxcbracketmenu.png)

**Stage Normal** will stage then as two pairs in the table

**Stage Sharing Car** will stage them as four individual runs in the table

**Override Dialins** will let you change the dialins from those initial calculated

Below you can see one round staged as two pairs and the next round staged as
single drivers shared a car

![Staged](images/fxcstaged.png)


## Activating a Row

Normally, the activated row will automatically advance downwards except for
when starting a new challenge.  To activate a new row or change the current
active row **RIGHT CLICK** on the row you want to activate and select **Make
Row Active**.

![StageMenu](images/fxcstagemenu.png)

The row will become highlighted indicating that is where the next runs will be
recorded.  If there was already an active row, it will confirm with you that
you want to change the active row.

![ActiveRow](images/fxcactiverow.png)

The data from the timer in the top right should also change to indicate the
dialins that are set for the next drop of the tree.

![TimerHeader](images/fxctimer.png)

If there is ever a time when the report from the timer (top right) and the
currently active row have different values for their dialins, the times in the
top right will become red.  This most likely indicates that there is a network
connection problem between the two computers.

## Moving a Row

If you need to move a row, either because they staged in wrong order or for
some other reason, you can simply click and drag the row to the new location.
If you need to activate the row, you can do so as per normal vai the context
menu.

![MoveRow](images/fxchallengemove.gif)

