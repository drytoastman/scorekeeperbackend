# Common Keyboard Wedge Scanner

**This style of barcode scanner is not recommended for DataEntry.**  As the scans come in as keyboard input outside
of the control of the data entry worker, it is possible that the scans get lost on other applications or mix with typing
from the worker.  Therefore, they work well for Registration but not DataEntry.

---

There are a lot of the common keyboard wedge barcode scanners out there.  Most of these plug into the USB port on the
computer and pretend to be a keyboard, 'typing' the characters from a scan.  There usually isn't a lot of configuration
to the scanner itself so we allow some configuration in the application.

To configure the application to use the scanner, select **Keyboard** as the scanner type and then verify the
**Keyboard Options** are set to match the scanner.  Some typical settings are:

 * STX start character
 * ETX end character
 * 100ms max delay

<span class='spacer100'></span>
![keyboardbarcodemenu](images/keyboardbarcodemenu.png)
<span class='spacer100'></span>
![keyboardbarcodeconfig](images/keyboardbarcodeconfig.png) 

