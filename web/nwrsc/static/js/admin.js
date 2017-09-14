
var saveids = Array();
var cars = Array();
var drivers = Array();

function newCountedRow(listform)
{
    var lastrow = $(listform + ' tr:last');
	var oldcount = lastrow.data('counter');
    var newrow = lastrow.clone();
    var newcount = oldcount+1;
	newrow.data('counter', newcount);
    newrow.find("input,select").attr("id", function(ix, val) { return val.replace(""+oldcount, ""+newcount); })
                               .attr("name", function(ix, val) { return val.replace(""+oldcount, ""+newcount); })
                               .val("");
    newrow.find("input[type=checkbox]").attr("value","y"); // I don't understand why but this is necessary
    newrow.find(".deleterow").click(function () { rowelem.remove(); return false; });
    newrow.appendTo(listform + ' tbody');
    return false;
}



function editdriver(did)
{
	$('#drivereditor').DriverEdit("doDialog", drivers[did], function() {
		$.nwr.updateDriver($("#drivereditor").serialize(), function() { 
			$("#driverlist").change();
		})
	});
}

function editcar(did, cid)
{
	$('#careditor').CarEdit('doDialog', did, cars[cid], function() {
		$.nwr.updateCar($("#careditor").serialize(), function() {
			$("#driverlist").change();
		})
	});
}

function deletedriver(did)
{
	$.post($.nwr.url_for('deletedriver'), { driverid: did }, function() {
		// Note ids to save and then rebuild driverlist and reselect, slow but always a sure sync with database
		saveids = $('#driverlist').val();
		for (var idx in saveids)
		{
			if (saveids[idx] == did)
			{
				saveids.splice(idx, 1);
				break;
			}
		}
		$.getJSON($.nwr.url_for('getdrivers'), {}, buildselect);
	});
}

function deletecar(cid)
{
	$.post($.nwr.url_for('deletecar'), { carid: cid }, function() {
		$("#driverlist").change(); // force reload of driver info
	});
}

function mergedriver(did, allids)
{
	$.post($.nwr.url_for('mergedriver'), { driverid: did, allids: allids.join(',') }, function() {
		saveids = [""+did];
		$.getJSON($.nwr.url_for('getdrivers'), {}, buildselect);
	});
}

function titlecasedriver(did)
{
	$.post($.nwr.url_for('titlecasedriver'), { driverid: did }, function() {
		$('option', $('#driverlist')).remove(); // fix for IE bug
		saveids = [""+did];
		$.getJSON($.nwr.url_for('getdrivers'), {}, buildselect);
	});
}

function titlecasecar(cid)
{
	$.post($.nwr.url_for('titlecasecar'), { carid: cid }, function() {
		$("#driverlist").change(); // force reload of driver info
	});
}

function collectgroups(frm)
{
    for (var ii = 0; ii < 3; ii++)
    {
        var x = Array();
        $("#group"+ii+" li").each(function() {
            x.push(this.innerHTML);
        });
        frm['group'+ii].value = ""+x;
    }
}

