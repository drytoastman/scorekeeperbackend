
function processData(json)
{
    if (json.modified > lasttime)
    {
        lasttime = json.modified;
        if (announcermini) {
            $('#firste').html(json.last);
            $('#runorder').html(json.order);
        } else {
            $('#seconde').html($('#firste').html());
            $('#firste').html(json.last);
            $('#nexte').html(json.next);
            $('#topnetcell').html(json.topnet);
            $('#toprawcell').html(json.topraw);
            $('#runorder').html(json.order);
            $('a[href="#firste"]').tab('show');
        }
    }
}

function classView(classcode)
{
    $('#specclass').html(classcode);
    $('a[href="#specclass"]').tab('show')
}

function updateCheck()
{
    $.ajax({
            dataType: "json",
            url: announcerbase + 'next',
            data: { modified: lasttime, mini: announcermini?1:0 },
            success: function(data) { processData(data); updateCheck(); },
            error: function(xhr) { if (xhr.status != 403) { setTimeout(updateCheck, 3000); } }
            });
}


function timerUpdate()
{
    $.ajax({
            dataType: "json",
            url: announcerbase + 'timer',
            data: { lasttimer: lasttimer },
            success: function(data) {
                if ('timer' in data)
                {
                    lasttimer = data.timer;
                    $('#timeroutput').text(lasttimer);
                }
                timerUpdate();
            },
            error: function(xhr) {
				if (xhr.status != 403) {
					setTimeout(timerUpdate, 3000);
				}
			}
    });
}

$(document).ready(function(){
    announcermini = (location.search.indexOf('mini=1') >= 0);
    announcerbase = location.protocol + '//' + location.host + location.pathname;
    lasttime = 0;
    lasttimer = "0.000";

    var modal = $('#classSelectModal');
    var input = modal.find('input');
    modal.removeClass('fade'); // make it snappier
    modal.on('hidden.bs.modal', function (e) { input.val(''); });
    modal.on('shown.bs.modal',  function (e) { input.trigger('focus'); })
    input.keypress(function (e) {
        if (e.key == 'Enter') {
            code = $(this).val();
            input.val('');
            modal.modal('hide');
            classView(code);
        }
    });

    $('body,.nav-link').keypress(function(e){
        if (e.target === this) {
            $('#classSelectModal').modal('show');
        }
    });

    updateCheck();
    if (!announcermini)
        setTimeout(timerUpdate, 1000);
});


