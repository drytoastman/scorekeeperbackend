
function setResult(rootid, data)
{
    $(rootid+' .class').html(data.class);
    $(rootid+' .champ').html(data.champ);
    $(rootid+' .entrant').html(data.entrant);
}

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
            if ('current' in json.lastresult) {
                $('#firste').html(json.lastresult.current.entrant + json.lastresult.current.class);
            } else {
                if ('left' in json.lastresult) {
                    $('#firste').html(json.lastresult.left + json.lastresult.class);
                } else {
                    $('#firste').html(json.lastresult.right + json.lastresult.class);
                }
            }
            $('#runorder').html(json.lastresult.order);
        } else {
            $('#seconde').html($('#firste').html());
            setResult('#firste', json.lastresult.current)
            setResult('#nexte', json.lastresult.next);
            $('#topnetcell').html(json.lastresult.topnet);
            $('#toprawcell').html(json.lastresult.topraw);
            $('#runorder').html(json.lastresult.order);
            $('a[href="#firste"]').tab('show');
        }
    }

    if ('lastclass' in json && json.lastclass.timestamp > Announcer.request.lastclass)
    {
        Announcer.request.lastclass = json.lastclass.timestamp;
        $('#specclass .class').html(json.lastclass.class);
        $('#specclass .champ').html(json.lastclass.champ);
    }
}

$(document).ready(function(){
    Announcer.request = {
        lastclass:  0,
        classcode:  "",
        lastresult: 0,
        lasttimer:  "0.000",
    };
    updateCheck();
});
