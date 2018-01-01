

function updateProfile() { $('#profilewrapper').nwr('loadProfile'); }
function updateCars() {
	if ($('#registercarform').is(':data(uiDialog)')) {
		$('#registercarform').dialog('destroy').remove(); // make sure we loose that link
	}
	$("#carswrapper").nwr('loadCars');
}
function updateEvent(eventid) {
	$('#event'+eventid).nwr('loadEvent', eventid, function() {
		eventPaneSetup($(this));
	});
 }
function updateAll() {
	updateCars();
	$('.eventholder.eventopen').each(function () {
		updateEvent($(this).data('eventid'));
	});
}

function unregButtons(jqe)
{
	jqe.find(".unregbutton").button({icons: { primary:'ui-icon-scissors'}, text: false} ).click(function () {
		$this = $(this);
		var regid = $this.data('regid');
		var eventid = $this.data('eventid');

		container = $('div.eventholder[data-eventid='+eventid+'] .carcontainer');
		container.find('ul,button,span.limit').remove();
		container.append("<div class='strong'>unregistering car ...</div>");
		$.nwr.unRegisterCar(regid, function() {
			updateCars();
			updateEvent(eventid);
		});
	});
}

function editCar(driverid, car) {
	$('#careditor').CarEdit('doDialog', driverid, car, function() {
		$.nwr.updateCar($("#careditor").serialize(), updateCars);  // don't update events, can't edit a car used anyhow
	});
}

function profileTabSetup()
{
	$(".editprofile").button().click( function() {
		$(this).blur();
		var driverid = $(this).data('driverid');
		$('#drivereditor').DriverEdit("doDialog", drivers[driverid], function() {
			$.nwr.updateDriver($("#drivereditor").serialize(), updateProfile);
		});
	});
}

function carTabSetup()
{
	$("#carlist .deletecar").button({icons: { primary:'ui-icon-trash'}, text: false} ).click(function() {
		var carid = $(this).data('carid');
		if (!confirm("Are you sure you wish to delete this car?"))
			return;
		$.nwr.deleteCar(carid, updateCars); // can only delete something not used in events 
	});
	
	$("#carlist .editcar").button({icons: { primary:'ui-icon-pencil'}, text: false} ).click(function() {
		var driverid = $(this).data('driverid')
		var car = cars[$(this).data('carid')];
		$(this).blur();
		editCar(driverid, car);
	});
	
	$("#carlist .regbutton").button().click( function() {
		var car = cars[$(this).data('carid')]; // pull from global that we set in template
		var thisbutton = $(this);
		thisbutton.blur();
		$("#registereventform").RegEdit('registerForEvent', car, 
			function() {
				thisbutton.parents('.carevents').html("<div class='strong'>registering for events ...</div>");
			},
			function() {
				updateCars();
				$('#registereventform input:checked').each(function() {
					updateEvent($(this).prop('name')); // the input name= contains the eventid
				});
			}
		);
	});
	
 	$('button.createcar').button().click(function() {
		$(this).blur();
		editCar($(this).data('driverid'), {}); 
	});

	unregButtons($('#carlist'));
}

function eventCollapsable()
{
	$('#eventsinner > h3').last().addClass('lastevent');
	$('#eventsinner > h3').click(function() {
		var h3 = $(this);
		var ev = $(this).next();
		
		if (ev.is(':visible')) {  // collapse, then add collapsed indicator
			ev.toggle('blind', function() { h3.addClass('collapsed'); });
		} else { // remove collapsed indicator, then show it
			h3.removeClass('collapsed');
			ev.toggle('blind');
		}
		$(this).find(".downarrow").toggle();
		$(this).find(".rightarrow").toggle();
	});
	$('#eventsinner > h3').filter(':not(.eventopen:first)').click(); // close all except first open event
}


function matchHeight(jqe)
{
	var height = 0;
	jqe.children().map(function() { height = Math.max($(this).height(), height); });
	jqe.children().css('min-height', height);
}

function eventPaneSetup(jqe)
{
	jqe.find('.regcarsbutton').button().click( function() {
		var eventid = $(this).data('eventid');
		var theevent = seriesevents[eventid];
		var regcars = 0;
		$.each(cars, function(i, car) { if ($.inArray(theevent.id, car.canregevents) < 0) { regcars++; } } );

		var limit;
		if (theevent.doublespecial) {  // if doublespecial and have a single entry (appear in canreg), they can reg up to perlimit
			limit = theevent.perlimit - regcars;
		} else {  // otherwise, the event limit is also counted
			limit = Math.min( theevent.totlimit - theevent.count, theevent.perlimit - regcars );
		}

		$(this).blur();
		$("#registercarform").RegEdit('registerCars', theevent, cars, limit, 
			function() {
				container = $('div.eventholder[data-eventid='+eventid+'] .carcontainer');
				container.find('ul,button').remove();
				container.append("<div class='strong'>registering cars ...</div>");
			},
			function() {
				updateCars();
				updateEvent(eventid);
			}
		);
	});

	unregButtons(jqe);
}

function loginPage()
{
    $("#loginForm").validate();
    $("#loginsubmit").button();
	$("#createdriver").button().click( function() {
		$('#drivereditor').DriverEdit("doDialog", {}, function() {
			$("#drivereditor").submit();
		});
	});
}


// Submit change requests via AJAX and then update the event section separately
function eventRelativeSubmit(form)
{
    form.closest('.modal').modal('hide');
    var eventid = form.find('input[name=eventid]').val();
    var targetdiv = $('#eventtog'+eventid);
    var sheight = targetdiv.height();
    targetdiv.html('<i class="fa fa-spinner fa-pulse fa-3x fa-fw text-center"></i>');
    targetdiv.height(sheight);

    $.ajax({
        dataType: "html",
        url: form.attr('action'),
        data: form.serialize(),
        method: 'POST',
        success: function(data) { targetdiv.html(data); },
        error: function(xhr, stat, error) { targetdiv.html('<div class="error">'+xhr.responseText+'</div>'); },
        complete: function(xhr) { targetdiv.height('auto'); }
    });
}


function initpaymentform(id, eventid)
{
    var me = $(id);
    var itemlist = gItems[gAccounts[eventid].id];
    var type = gAccounts[eventid].type;
    var regcars = gRegistered[eventid];

    me.find('.paypal-row').hide();
    me.find('.square-row').hide();
    me.find('.'+type+'-row').show();
    me.find('.error').text("");
    me.find('input[name=eventid]').val(eventid);

    me.find('select').each(function(index) {
        var select = $(this);
        var container = select.closest("div.row");

        select.find('option').remove(); 
        select.append($('<option>').attr('value', '').text('No Payment'));

        // If the car isn't registered or already paid, hide from the available list
        try {
            var rowid = container.attr('id').substring(7);
            var found = false;
            $.each(regcars, function() {
                if (this.carid != rowid) return;
                if (this.payments > 0) throw 'Already paid';
                found = true;
            });
            
            if (!found) throw 'Not registered';
        } catch (e) {
            container.css('display', 'none');
            return;
        }

        container.css('display', 'flex');
        $.each(itemlist, function() {
            select.append($('<option>').attr('value', this.itemid).text(this.name + " - $" + (this.price/100).toFixed(2)));
        });
    });
}


function initregform(id, eventid, limit, msg)
{
    var me = $(id);
    var checkmax = function() {
        var dodisable = (me.find(":checked").length >= limit);
        me.find('input[type=checkbox]:unchecked').prop('disabled', dodisable);
        me.find('.statuslabel').html( dodisable && msg || "");
    };

    me.find('input[name=eventid]').val(eventid);
    me.find('input[type=checkbox]').prop('checked', false).prop('disabled', false).click(checkmax);
    gRegistered[eventid].forEach(function (regentry) {
        me.find("input[name="+regentry.carid+"]").prop('checked', true);
    });

    checkmax();
}


