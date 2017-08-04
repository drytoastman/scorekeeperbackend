<%inherit file="/base.mako" />

<ul id='adminmenu' class='sf-menu'>
<li id='titlebutton'><a>${c.seriesname}</a></li>
<li><a href='javascript:void(0);'>Event Admin</a>
	<ul>
	%for event in sorted(c.events, key=lambda obj: obj.date):
		<li><a href='${h.url_for(eventid=event.id, action='')}'>${event.name}</a></li>
	%endfor
	</ul>
</li>
<li><a href='javascript:void(0);'>Series Admin</a>
	<ul>
	<li><a href='${h.url_for(eventid='s', action='createevent')}'>New Event</a></li>
	<li><a href='${h.url_for(eventid='s', action='classlist')}'>Classes</a></li>
	<li><a href='${h.url_for(eventid='s', action='indexlist')}'>Indexes</a></li>
	<li><a href='${h.url_for(eventid='s', action='seriessettings')}'>Settings</a></li>
	<li><a href='${h.url_for(eventid='s', action='passwords')}'>Passwords</a></li>
	<li><a href='${h.url_for(eventid='s', action='invalidcars')}'>Invalid Cars</a></li>
	<li><a href='${h.url_for(eventid='s', action='fieldlist')}'>Driver Fields</a></li>
	<li><a href='${h.url_for(eventid='s', action='drivers')}'>Driver/Car Editor</a></li>
	<li><a href='${h.url_for(eventid='s', action='recalc')}'>Recalculate Results</a></li>
	<li><a href='${h.url_for(eventid='s', action='purge')}'>Purge Tool</a></li>
	</ul>
</li>
<li><a href='javascript:void(0);'>Reports</a>
	<ul>
	<li><a href='${h.url_for(eventid='s', action='newentrants')}' target='_blank'>Event Fees/New Entrants</a></li>
	<li><a href='${h.url_for(eventid='s', action='contactlist')}'>Series Contact List</a></li>
	<li><a href='${h.url_for(eventid='s', action='weekend')}'>Weekend Entries</a></li>
	</ul>
</li>
<li><a href='javascript:void(0);'>Other</a>
	<ul>
	<li><a href='${h.url_for(eventid='s', action='copyseries')}'>Create Series From Current</a></li>
	</ul>
</li>
</ul>
<br clear='all'/>

%if c.isLocked:
<div class='ui-state-error'>
<span class='ui-state-error-text'>
Locked
</span>
</div>
%endif

<div class='body ui-widget'>
${next.body()}
</div>

