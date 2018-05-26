
function processData(json)
{
    if ('lasttimer' in json)
    {
        Announcer.request.lasttimer = json.lasttimer;
        $('#timeroutput').text(json.lasttimer);
    }

    if ('lastresult' in json && json.lastresult.timestamp > Announcer.request.lastresult)
    {
        Announcer.request.lastresult = json.lastresult.timestamp;
        if (Announcer.mini) {
            $('#firste').html(json.lastresult.last);
            $('#runorder').html(json.lastresult.order);
        } else {
            $('#seconde').html($('#firste').html());
            $('#firste').html(json.lastresult.last);
            $('#nexte').html(json.lastresult.next);
            $('#topnetcell').html(json.lastresult.topnet);
            $('#toprawcell').html(json.lastresult.topraw);
            $('#runorder').html(json.lastresult.order);
            $('a[href="#firste"]').tab('show');
        }
    }

    if ('lastclass' in json && json.lastclass.timestamp > Announcer.request.lastclass)
    {
        Announcer.request.lastclass = json.lastclass.timestamp;
        $('#specclass').html(json.lastclass.last);
    }
}

function classView(classcode)
{
    Announcer.request.classcode = classcode;
    Announcer.request.lastclass = 0;
    $('#specclass').html("Loading " + classcode);
    $('a[href="#specclass"]').tab('show')
    updateCheck();
}

function updateCheck()
{
    Announcer.inflight = $.ajax({
        beforeSend : function() { if(Announcer.inflight != null) { Announcer.inflight.abort(); } },
        dataType: "json",
        url:      Announcer.base + 'next',
        data:     Announcer.request,
        success:  function(data) { processData(data); updateCheck(); },
        error:    function(xhr) { if ((xhr.status != 403) && (xhr.status != 0)) { setTimeout(updateCheck, 3000); } }
    });
}

var Announcer = {};

$(document).ready(function(){
    Announcer.mini = (location.search.indexOf('mini=1') >= 0);
    Announcer.base = location.protocol + '//' + location.host + location.pathname;
    Announcer.inflight = null;
    Announcer.request = {
        lastclass:  0,
        classcode:  "",
        lastresult: 0,
        lasttimer:  "0.000"
    };

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
});
