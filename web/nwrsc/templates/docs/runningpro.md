# Running a ProSolo Event

1. Registration will have their own laptop, they will merge data later
    * After registration closes, verify that any pregregistered entrants who didn't show have been removed from registration
    * Registration must also verify that all single/first drivers use numbers 1-99 and that all second drivers use 101-199
    * <span style='color:red'>The above two points are important or the grid report will be wrong</span>

2. Setup 3 laptops with power and network connections along with PA, etc
    * Laptop 1 will become DataEntry for left side
    * Laptop 2 will become DataEntry for right side
    * Laptop 3 will become ProTimer and requires some form of serial port.  You can run **StartProTimer.bat** instead of starting Scorekeeper itself.
      Connect to Jerry's hardware and test to see if commands are actually being sent over serial line.

3. Setup data entry laptop(s)
    * Make sure data entry laptop is running and connected to the network, by cable is preferred but not necessary
    * Set event to proper, course=1 (Left side) or course=2 (Right side)
    * Timer => Pro Timer network, select the ProTimer service that is found.
      If nothing is found, verify ProTimer is on and connected to the network and that firewalls are not an issue (**rules.bat** is useful here)
    * In the Scorekeeper System Window, you should see the other Data Entry machine as a entry in the **Active Hosts** table.
      This means that they can sync with each other as the event progresses.

4. Print out grid reports (after registration merges updates)
    * Go to the admin page on the data entry machine (<http://127.0.0.1/admin/>)
    * From the menu bar, select Event&rarr;(EventName)
    * Click on Grid Order
    * Drag and drop classes into their associated groups (1 or 2) and order and then click **Update**
    * Click on the **grid report by number** shortcut to get the grid report on its own page and print for the grid chief.  A second copy can be made for timing if necessary.

5. Proceed similar to regular data entry
    * When using two data entry machines, it’s just like a regular event.  With a single machine, the user must flip back and forth between course 1 and 2.
    * Each machine is connected to the ProTimer will get left times and right times but left times only show when course 1 is selected and right times only show when course 2 is selected.
    * See the [Data Entry](dataentry.md) and [Data Entry Pro](dataentry-pro.md) pages for more info.

6. As each run group ends, perform audit
    * Standard run group print out.  Should open two tabs in the browser, one for course 1 and one for course 2.

7. After first half, print out new grid report
    * Go to the results page on the data entry machine (<http://127.0.0.1/results/>)
    * Select the current event and click on Grid Order by Standings and print out for grid chief
    * You can use **Reorder by Net** from the ProSolo menu to reorder the run order automatically, see the [Data Entry Pro](dataentry-pro.md) page for details.

8. Perform final audit

9. Print dialin report from the results page on the data entry machine (<http://127.0.0.1/results/>)

10. See the challenge document for running challenges.


