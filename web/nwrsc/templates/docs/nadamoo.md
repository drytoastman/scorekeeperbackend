# Nadamoo Barcode Scanner

We are currently using the NADAMOO 433Mhz Wireless Barcode Scanner.  The frequency allows a better range and its only about $40.
The following are some recommended settings for the Nadamoo scanner.  You can print this page out and then scan the following barcodes
if you don't have the instruction booklet with you. 

<table class='barcodes'>
<tr>
<td><svg id='restoreefaults'></svg>
<td><svg id='virtualcom'></svg>
<td><svg id='instantupload'></svg>
</tr>
<tr>
<td><svg id='highvolume'></svg>
<td><svg id='standby10'></svg>
<td><svg id='shutoff5'></svg>
</tr>
</table>

<script>
JsBarcode("#restoreefaults", "\xC901B",        { text: "Restore Defaults",        format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#highvolume",     "\xC90114205",    { text: "High Volume",             format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#standby10",      "\xC90119905001", { text: "10 Seconds To Stanbdy",   format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#shutoff5",       "\xC90119906030", { text: "5 Minutes To Switch Off", format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#instantupload",  "\xC901199000",   { text: "Instant Upload",          format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#virtualcom",     "\xC9011991501",  { text: "USB Virtual COM",         format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
</script>

First start by reseting to defaults, setting the interface to a COM (serial) port and enabling Instant Upload to make sure that is
upload right away rather than storing in the scanner.  Other useful options include setting to the beep indicator to its highest volume,
setting a quick standy (10 seconds) and a longer switch off (5 mins) so that the user doesn't have to deal with the turn on beep for every scan.

To configure Registration or Data Entry to use the scanner, select **SerialPort** as the scanner type and then verify the **SerialPort Options**
are set to:

 * no start character
 * carriage return end
 * 100ms max delay


<span class='spacer100'></span>
![serialbarcodemenu](images/serialbarcodemenu.png)
<span class='spacer100'></span>
![serialbarcodeconfig](images/serialbarcodeconfig.png) 

