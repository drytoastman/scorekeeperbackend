# Data Entry

## Barcodes

### Scanned Codes
Scanned barcodes received via the keyboard or serial port input are used to search the list of drivers based on their barcode value.
This is usually an SCCA membership number as some drivers already have those on their helmet but it can be any number.

### Manual Barcode Entry
Ctrl+B brings up a barcode field.  Entering a barcode into this field and hitting Enter is the same as someone scanning the
barcode with a barcode scanner.

### Placeholder Entries
Any time an applicable driver and/or car entry can not be matched to a barcode entry, a placeholder value is substitued so the user can 
continue without interruption.  This can be just an placeholder car (1st entry below) or a driver and car (2nd entry below).  These
placeholder should be swapped with the correct entrant when the user has time.  Once a placeholder is no longer in use, either by
removing it from the runorder or swapping in the correct car, the program will ask you if you want to delete it automatically as seen below.

![Placeholders](images/placeholders.gif)


## Preregistered Quick Entry
The quick entry for printed cards from the previous version of Scorekeeper has been modified.  The carid field is now a UUID
and not very quick to type in.  The number printed on the timing cards is an integer subset of the car identifier.

Ctrl+Q now opens a quick entry tab in the left side of the screen and places focus on the text field.  This quick entry tab
contains a list of all the registered entrants.  As you type numbers from the beginning of the number at the top of the timing
card, this list is reduced to entrants that match. 

![QuickEntryTab](images/quickentryfield.gif)

The first entry is always selected.  Usually within 3 - 4 numbers, the list
is reduced to a single entry.  The Enter key will add the selected value to the run order.  You can also double click an entry
to select it.


## Filtering Table
Ctrl+F brings up a filter field.  Entering data into this field will filter the table entry by matching the field with the
driver name, car number, class and description or even times.  Closing the filter field with Esc or the x icon automatically
clears the filter.

![TableFilter](images/dataentryfilter.gif)

## Change Driver/Car
To correct a car or driver, first find the driver in the rungroup and double click the driver column. This
will bring up the driver and car in the manual entry tab. Either select the correct driver and car from
the lists or create a new ones as needed. When the correct values are selected, click “Swap Entrant”.

## Run Errors
To correct a run error is the same as correcting a time during data entry. Find the time in the rungroup,
double click it to load the values into the entries on the right side of the screen, fix as needed and click
enter.

## Auditing
To perform auditing, select: **Reports -> Current Group Audit -> Order**, where order is the order you would like them printed out.

The values on the audit report are the **RAW** times plus any cones and gates. These values should match the raw values
on the timing card. For each person, verify all of their times with the audit report. If something doesn't match up,
you will need to determine which value is wrong and correct it.

