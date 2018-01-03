{% set cda = classdata.getJSONArrays() %}
var thetable = Object();
var currentcars = Object();
var gClasses = {{cda[0]|safe}};
var gIndexes = {{cda[1]|safe}};

const EDIT  = 1
const DEL   = 2
const MERGE = 3
const DRV = 4
const CAR = 5

function resizescroll() 
{
	$('.dataTables_scrollBody').css('height', $(window).height() - ($('body').height() - $('.dataTables_scrollBody').height())- 10);
}

function selecteddrivers(tofilter)
{
    return thetable.rows({selected:true}).data().filter(function (x) { return x.driverid != tofilter; }).map(function (x) { return ""+x.driverid; }).join();
}

function baction(atype, atarget, arg, disable)
{
    var text = "?";
    switch (atype) {
        case EDIT:  text = "Edit"; break;
        case DEL:   text = "Delete"; break;
        case MERGE: text = "Merge Into This"; break;
    }

    return $('<button>').addClass('btn btn-outline-admin small').text(text).prop('disabled', disable).click(function() {
        switch (atype) {
            case MERGE:
                var driverids = selecteddrivers(arg);
                $.ajax({
                    url: "{{url_for('.mergedrivers')}}",
                    data: { dest:arg, src:driverids },
                    method: 'POST',
                    success: function(data) {
                        thetable.rows('#'+driverids.split(',').join(',#')).remove().draw();
                        thetable.row('#'+arg).select();
                    },
                    error: function(xhr, stat, error) { alert(xhr.responseText); },
                });
                break;

            case DEL:
                $.ajax({
                    url: "{{url_for('.deleteitem')}}",
                    data: (atarget == DRV) ? {driverid:arg} : {carid:arg, series:currentcars[arg].series},
                    method: 'POST',
                    success: function(data) { thetable.row('#'+arg).deselect(), $('#'+arg).remove(); },
                    error: function(xhr, stat, error) { alert(xhr.responseText); },
                });
                break;

            case EDIT:
                if (atarget == DRV) {
                    load_driver_form($('#profileform'), thetable.row('#'+arg).data());
                    $('#profilemodal').modal('show');
                } else {
                    $('#carform').CarEdit('initform', currentcars[arg]);
                    $('#carform').data('series', currentcars[arg].series);
                    $('#carmodal').modal('show');
                }
                break;
        }
    });
}

function buildEntrantTable(driver, cars, series, disabledelete, disablemerge)
{
    var table = $('<table>').addClass('drivertable');
    table.append($('<tr>').append($('<td>').prop('colspan', 2).addClass('buttons').append(baction(EDIT, DRV, driver.driverid, false), baction(DEL, DRV, driver.driverid, disabledelete), baction(MERGE, DRV, driver.driverid, disablemerge))));
    table.append($('<tr>').append($('<th>').text('DriverId'),   $('<td>').text(driver.driverid)));
    table.append($('<tr>').append($('<th>').text('Name'),       $('<td>').text("{0} {1}".format(driver.firstname, driver.lastname))));
    table.append($('<tr>').append($('<th>').text('Email'),      $('<td>').text(driver.optoutmail ? "*******" : driver.email)));
    table.append($('<tr>').append($('<th>').text('Membership'), $('<td>').text(driver.membership)));
    table.append($('<tr>').append($('<th>').text('Address'),    $('<td>').text("{0} {1} {2} {3}".format(driver.address, driver.city, driver.state, driver.zip))));
    for (ii in cars) {
        var c = cars[ii];
        var label1 = $('<span>').addClass('cardetails').text("{0} #{1} {2} {3} {4} {5}".format(c.classcode, c.number, c.year, c.make, c.model, c.color));
        var label2 = $('<span>').addClass('carseries').text(c.series);
        table.append($('<tr>').addClass('carrow').append($('<td>').prop('colspan', 2).prop('id', c.carid).append(baction(EDIT, CAR, c.carid, false), baction(DEL, CAR, c.carid, c.activity>0), label1, label2)));
    }
    if (series != undefined && series.length > 0) {
        table.append($('<tr>').addClass('seriesrow').append($('<td>').prop('colspan', 2).text("*Has cars in " + series)));
    }
    return table;
}

function rebuildInfoContainer()
{
    driverids = selecteddrivers();
    targetdiv = $('#driverinfo');
    targetdiv.html("")
    if (driverids.length > 0) {
        $.ajax({
            url: "{{url_for('.getitems')}}",
            data:   {driverids:driverids},
            method: 'GET',
            success: function(data) {
                currentcars = Object();
                var seriesact = Object();
                var drivercount = 0;
                for (driverid in data) {
                    if ('series' in data[driverid])
                        seriesact[driverid] = data[driverid]['series'].length > 0;
                    drivercount += 1;
                }
                for (driverid in data) {
                    driver = thetable.row('#'+driverid).data();
                    var caract = false;
                    for (var idx in data[driverid]['cars']) {
                        var c = data[driverid]['cars'][idx];
                        currentcars[c.carid] = c;
                        if (c.activity > 0) {
                            caract = true;
                        }
                    }
                    var otherseriesact = false;
                    for (did in seriesact) {
                        otherseriesact |= (did != driverid) && seriesact[did];
                    }
                    targetdiv.append(buildEntrantTable(driver, data[driverid]['cars'], data[driverid]['series'], caract > 0, (drivercount<2) || (otherseriesact>0)));
                }
            },
            error: function(xhr, stat, error) {
                targetdiv.html('<div class="error">'+xhr.responseText+'</div>');
            },
        });
    }
}

// Override the standard form submit to ajax
function modalupdate(e) {
    e.preventDefault();
    var form = $(this)
    var isdriver = form.find('input[name=firstname]').length > 0;
    var driverid = form.find('input[name=driverid]').val();
    var series = form.data('series');
    var data = form.serialize();
    if (series != undefined)
        data += '&series='+series;

    $.ajax({
        url: form.prop('action'),
        method: form.prop('method'),
        data: data,
        success: function(data) {
            // hide the modal, update the datatables info with any driver change, and rerequest selected items
            form.closest('.modal').modal('hide')
            if (isdriver) thetable.row('#'+driverid).data(form.serializeArray().reduce(function(m,o) { m[o.name] = o.value; return m; }, {}));
            rebuildInfoContainer();
        },
        error: function(xhr) {
            alert(xhr.responseText);
        },
    });
}

$(document).ready(function(){
    thetable = $('#drivertable').DataTable({ 
        ajax: { url:"{{url_for(".getdrivers")}}", dataSrc: ''},
        paging: false,
        scrollY: "100",
        select: {
            style: 'os',
        },
        rowId: 'driverid',
        columns: [
            { data: 'firstname' },
            { data: 'lastname' },
        ],
        sDom: '<"dtheader"f>rt<"clear">'
    }).on('select.dt deselect.dt', function () {
        rebuildInfoContainer();
    });

	resizescroll();
	$( window ).resize(function() { resizescroll(); });
    $('#profileform, #carform').submit(modalupdate);
});

