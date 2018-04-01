# Registration

## Initial download or sync

Download/Merge from the [sync tool int the status window](sync.md)

## Setup Verification 

Select the event you are administering. You can check the Lock checkbox to disable event selection so that
accidental event selection does not occur during registration activity.

![EventLock](images/reglock.png)

## Standard Actions

1. Do one of the following:
    * scan the driver's barcode to go directly to the driver's information
    * enter part of the first and/or last name, more name information produces a shorter list of drivers in the next step

    ![SearchBox](images/regsearch.png)

2. If not scanning a barcode, select the driver from the list of drivers
    * If the name is not present, you must click New Driver to create a new driver entry 

    ![DriverEntry](images/regdriver.png)

3. You can **Edit Driver** to update the member information
    * The barcode number is important if you intend to use barcode scanning 
    * If a barcode is needed, click Print Label to print to the selected printer device - make sure correct printer is selected.

4. Verify the correct car(s), class(es) and index are registered. 
    * Default status icons for preregistered drivers is the black checkmark as seen in the legend.  If they paid online, an amount will show next to the car.
    * Cars can be created, edited or deleted. 
        * **New From** prefills the data with the selected car - which can then be edited as needed (saves having to enter all car info if it only needs a different class or car number) 
        * The car dialog number field includes a colored square indicator to aid the registration worker
            * Green - number is avaiable
            * Yellow - number is used by another driver though the application won't stop the worker from using it
            * Gray - no data or number provided

    * To change a car entry, select it and click one of the activity buttons
        * **Register/Make Payment** sets the car status to registered and will ask for the amount paid
        * **Register Only** sets the car status to registered only
        * **Unregister** will unregister the car and is only available if the car is registered and *NOT* paid for yet
        * **Move Registration/Payments** is a special case to move payments from one car to another (i.e. they paid online for one car but moved to another onsite)

    * Entries that have a paid amount of $0.00 can be flagged in data entry
    * The list of payments for a car are listed on the right panel

    ![CarEntry](images/regcars.png)

## Reports

The number use and payment reports are available from the admin page.  Quick access to these pages are available under the Reports menu in registration.

## Merging

If select multiple cars that have the same class and index, a merge button will appear that merges the cars together.
The same option does not exist for drivers as the data is shared between other series on the main server so the merge
operation for drivers is only provided via the admin website.

## Syncing databases

Take laptops where they are in network range of the data entry machine and [sync via the scorekeeper status window again](sync.md)

