# Registration

## Initial download or sync

Download/Merge from the [sync tool int the status window](sync.md)

## Setup Verification 

* Select the event you are administering. You can check the Lock checkbox to disable event selection so that accidental event selection does not occur during registration activity.
    ![EventLock](images/reglock.png)
* If using a barcode scanner, verify that the scanner is connected and [setup](http://127.0.0.1/docs/commonbarcodescanner.md)


## Quick Overview

1. Scan or enter part of the drivers name to locate them
1. Verify any necessary driver and registered car information
1. Modify or add new information if necessary

## Driver Selection 

1. Do one of the following:
    * scan the driver's barcode to go directly to the driver's information
    * enter part of the first and/or last name, more name information produces a shorter list of drivers in the next step

    ![SearchBox](images/regsearch.gif)

1. If not scanning a barcode, select the driver from the list of drivers. If the name is not present, you must click **New Driver** to create a new driver entry 

1. You can **Edit Driver** to update the member information, the password field is left blank unless you are setting a new password

    ![EditDriver](images/editdriver.png)

1. If a barcode is needed, verify the label display and click Print Label to print to the selected printer device - make sure correct printer is selected.

    ![PrintBarcode](images/printbarcode.png)

1. Any red boxes such as **No Barcode** and **Duplicate Barcode** indicate things that you may need to attend to.

    ![NoBarcode](images/nobarcode.png)
    ![DuplicateBarcode](images/duplicatebarcode.png)


## Weekend Membership (optional based on series)

1. If SCCA weekend memberships are configured for the series, there will be a **Weekend Membership** button.

1. If the button has the card ![Card](images/card.png) icon, there is already an weekend membership assigned for the current time period. Clicking on the button will display the current weekend membership number.

1. If they don't have an active weekend membership, you can assign a new weekend membership number from the allotted pool.
    * Click **Weekend Membership** to open the dialog
    * Click **Assign New Membership**
    * Make sure the remembered fields contain the correct worker information
    * Click OK and the new number will be displayed.

    ![Weekend](images/weekend.gif)


## Car Selection

### Verifying the Entries

   ![CarEntry](images/regcars.png)

   * The registration icon ![RegIcon](images/reg.png) indicates that the car is registered for the event
   * A green dollar amount (<span style='color:green'><b>$12.34</b></span>) indicates that they entry has been paid for
   * An orange star icon ![StarIcon](images/star.png) indicates the car has activity in other events
   * A grayed out entry with **In Event** over it means that the car is being used in the current event and cannot be changed

   ![InEvent](images/inevent.png)


### Creating, Editing or Deleting Cars

   * **New Car** opens the new car dialog with blank fields
   * **New From** prefills the data with the selected car - which can then be edited as needed (saves having to enter all car info if it only needs a different class or car number) 
   * **Edit Car** allows changes to select cars to be made, cars that are already in use cannot be edited or deleted
   * **Delete Car** deletes unused cars from the list

   ![CarDialog](images/cardialog.png)

   The car dialog number field includes a colored square indicator to aid the registration worker
       * Green ![green](images/numbergreen.png) number is available
       * Yellow ![yellow](images/numberyellow.png) number is used by another driver though the application won't stop the worker from using it
       * Gray - no data or number provided

### Registering and/or Paying

   * **Register/Make Payment** sets the car status to registered and will add a new onsite payment to the entry
   * **Move Registration/Payments** is a special case to move payments from one car to another (i.e. they paid online for one car but moved to another onsite)
   * **Delete a Payment** lets you delete mistaken onsite payments from a list
   * **Register Only** sets the car status to registered only
   * **Unregister** will unregister the car and is only available if the car is registered and *NOT* paid for yet

   * Entries that have a paid amount of $0.00 can be flagged in data entry based on configuration


## Reports

The number use and payment reports are available from the admin page.  Quick access to these pages are available under the Reports menu in registration.

## Merging

If select multiple cars that have the same class and index, a merge button will appear that merges the cars together.
The same option does not exist for drivers as the data is shared between other series on the main server so the merge
operation for drivers is only provided via the admin website.

## Syncing databases

Take laptops where they are in network range of the data entry machine and [sync via the scorekeeper status window again](sync.md)

