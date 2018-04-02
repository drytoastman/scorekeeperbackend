# Challenge

**<span style='color:red'>THIS NEEDS TO BE UPDATED</span>**

## Initial Setup

Open the challenge GUI. Open the correct series if not already selected. Select the appropriate
event from the pull down list of events.  Initially, there will not be any challenges to select.

![ChallengeLoad](images/challengeload.png)

From the Challenge Menu, select New Challenge. You will be asked to select a name and the size of
the bracket. This will always be a power of 2 (4, 8, 16, 32). If the number of drivers is not a
power of 2, you can select the next largest size for the bracket.

Once the new challenge has been created, go to the challenge menu again and select Auto Load
Current. This will bring up a dialog letting you select the drivers to add.

Set the number of drivers for the challenge in the top number selection. For most instances, this
will be the size of the bracket but it could be a few drivers less in other situations. This setting
will verify that you select the correct number of drivers.

Underneath that, select which sets of drivers you are interested in loading, Ladies classes and Open
classes (non-ladies classes). You can also select whether to use bonus dialins (everyone users their
own dialin) or not (everyone uses their classes leaders dialin * index ratio).

Selecting drivers is done by holding the Ctl key and clicking or dragging across drivers. If you
wish to order the list by name or class, click on the column header to do so. Once you have selected
enough drivers, click OK. The bracket will be filled with the drivers selected and bracketed based
on their net times. You may also drag and drop drivers from the tree on the left of the main window
to enter them into a challenge but this is much more cumbersome.

Once, the challenge is ready, it may look something like so:

![ChallengeInitial](images/challenge1.png)

You will notice that there is a large red label in the top right indicating that the Challenge GUI
is not connected to the Timer. When this occurs, the GUI can't set dial in times and the results
won't make it back to the GUI. To remedy this, select Connect from the Timer menu.

![ChallengeTimer](images/challengetimer.png)

The connect dialog will pop up with all of the ProTimer services it can find on the network. There
should be only 1. If nothing appears, you must verify that the firewall on either computer isn't
interfering. Once selected, click OK and a connection will be made and the red label will disappear.

## Running a Challenge

To run a challenge, you open up each round as the entrants pull up to the line by clicking the Open
button for the corresponding round in the challenge tree.

![Stage](images/stage.png)

In this case, it expects Kit to be starting on the left side and Karl to be starting on the right
side. If they come up in different lanes, click the Swap checkbox and they will be swapped in the
window. Before the starter can start the round, you must click Stage. This will send the dial in
commands to the ProTimer laptop. If the hardware approves, the dialins will appear at the top of the
ProTimer window. If not, you can try clicking stage again to resend them.

Once staged, the runs will have colored, labeled and numbers indicators. Green/1 indicates where the
next set of run data to be received will be put. Purple/2 indicates the next location after that.
Once a run is entered, you will see the green box return to white and the purple box turn to green.
If there were cones or a DNF called, the operators must manually enter those by selecting the
appropriate value. Not Staged and Red Light errors will automatically be entered once the driver
passes through the finish lights. Once a round is over, the winner is automatically moved to the
next round along with their dialin. If the driver broke out, their new dialin is calculated and used
in the next round.

You can also stage the next set of competitors while the current set is finishing their second runs.
There colors will start out as Purple/2 and Red/3 as the next set of runs still belong to the
running round.

![Stage](images/stagemulti.png)

In special cases, there are some other options you can use:

* The Dial button under each driver can be used to override the dialin for the driver in that round.
  This must be done before clicking stage.
* The Reset Round button can be used to remove all run data from the round if something went wrong
  and it has to be restarted.
* If a driver doesn't show up for the round, clicking AutoWin under the driver that did show up will
  move them to the next round.
* Entering a raw time into one of the run time boxes lets you overwrite the time that came from the
  hardware or if no time arrived due to a network error.
* Clicking on of the run indicator buttons will bring up a dialog to let you change where the next
  runs will be placed. Deactivate is the same as assigning the run nothing and progressing as normal.
  Activate as next target will override current settings and make the selected run the next target.

![Stage](images/stageoverride.png)

## Understanding the Display
For the announcer, they are most concerned with the active round window. The main window will contain
the entire challenge tree but the results appear in each round window. Initially, the only useful
data will be the orange box. As the first half of the round ends, the top half of the results become
available. After the second round ends, all the results will be available.

* Orange box is the drivers name and dialin
* Red box is the difference from their dialin for the individual run, includes cone penalty
* Blue boxes are the results of one half of a round, value in parenthesis is without cones
* Green box is the final result of the entire round, this field will also indicate a breakout and
  new dialin

![Stage](images/challenge2.png)

