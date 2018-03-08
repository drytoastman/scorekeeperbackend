# Nadamoo Barcode Scanner

The follow are some recommended settings for the Nadamoo scanner.  First start by reseting to defaults:

<svg id='restoreefaults'></svg>

Set the interface to a COM port instead of keyboard input:

<svg id='virtualcom'></svg>

Make sure that is upload right away rather than storing in the scanner:

<svg id='instantupload'></svg>

Ensure that the beep volume is on high:

<svg id='highvolume'></svg>

And some power options that are up to you:

<svg id='standby30'></svg>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<svg id='shutoff5'></svg>

<script>
JsBarcode("#restoreefaults", "\xC901B",        { text: "Restore Defaults",        format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#highvolume",     "\xC90114205",    { text: "High Volume",             format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#standby30",      "\xC90119905003", { text: "30 Seconds To Stanbdy",   format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#shutoff5",       "\xC90119906030", { text: "5 Minutes To Switch Off", format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#instantupload",  "\xC901199000",   { text: "Instant Upload",          format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
JsBarcode("#virtualcom",     "\xC9011991501",  { text: "USB Virtual COM",         format: "CODE128B", width: 1, height: 50, fontSize: 12, textAlign: 'left' });
</script>

