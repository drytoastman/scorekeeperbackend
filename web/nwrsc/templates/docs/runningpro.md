# Running a ProSolo Event

**<span style='color:red'>This page needs to be updated</span>**

1. Registration will have their own laptop, they will merge data later

2. Setup 3 laptops with power and network connections along with PA, etc
    * Laptop 1 will become DataEntry for left side (or both) 
    * Laptop 2 will become ProTimer and requires some form of serial port.  Connect to Jerry's hardware and test to see if commands are actually being sent over serial line.
    * Laptop 3 (optional for right side) will DataEntry for the right side

3. Setup data entry laptop(s)
    * Make sure data entry laptop is running and connected to the network
    * Set event to proper, course=1 (Left side) or course=2 (Right side)
    * Timer => Pro Timer network, select the ProTimer service that is found.  If nothing is found, verify ProTimer is on and connected to the network and that firewalls are not an issue.

4. Print out grid reports (after registration merges updates)
    * Go to the admin page on the data entry machine (<http://127.0.0.1/admin/>), Event=>(EventName).  Click on Grid Order.  Drag and drop classes into their associated groups (1 or 2) and then click submit
    * Click on the "grid report by number" shortcut to get the grid report on its own page and print for the grid chief.  A second copy can be made for timing if necessary.

5. Proceed similar to regular data entry
    * If using two data entry machines, it’s just like a regular event.  With a single machine, the user must flip back and forth between course 1 and 2.
    * Each machine is connected to the ProTimer will get left times and right times but left times only show when course 1 is selected and right times only show when course 2 is selected.

6. As each run group ends, perform audit
    * Standard run group print out.  Should open two tabs in the browser, one for course 1 and one for course 2.

7. After first half, print out new grid report
    * Go to the results page on the data entry machine (<http://127.0.0.1/results/>)
    * Select the current event and click on Grid Order by Standings and print out for grid chief

8. Perform final audit

9. Print dialin report

10. See the challenge document for running challenges.


