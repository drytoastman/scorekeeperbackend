
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

function displayemail(data, type, row, meta) 
{
    if (row['optoutmail']) {
        return "**********";
    } else {
        return data;
    }
}

