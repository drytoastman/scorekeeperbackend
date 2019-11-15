
function processData(json)
{
    if ('lastresult' in json && json.lastresult.timestamp > Announcer.request.lastresult)
    {
        Announcer.request.lastresult = json.lastresult.timestamp;
        if ('left' in json.lastresult)
            $('#leftentrant').html(json.lastresult.left);
        if ('right' in json.lastresult)
            $('#rightentrant').html(json.lastresult.right);

        if ('leftnextfinish' in json.lastresult)
            $('#leftnextfinish').html(json.lastresult.leftnextfinish);
        if ('rightnextfinish' in json.lastresult)
            $('#rightnextfinish').html(json.lastresult.rightnextfinish);

        $('#classresult .class').html(json.lastresult.class);
        $('#classresult .champ').html(json.lastresult.champ);
        $('#topnetcell').html(json.lastresult.topnet);
        $('#topnetcell1').html(json.lastresult.topnet1);
        $('#topnetcell2').html(json.lastresult.topnet2);
        $('#toprawcell').html(json.lastresult.topraw);
        $('#toprawcell1').html(json.lastresult.topraw1);
        $('#toprawcell2').html(json.lastresult.topraw2);
        $('a[href="#firste"]').tab('show');
    }

    if ('lastclass' in json && json.lastclass.timestamp > Announcer.request.lastclass)
    {
        Announcer.request.lastclass = json.lastclass.timestamp;
        $('#specclass .class').html(json.lastclass.class);
        $('#specclass .champ').html(json.lastclass.champ);
    }

    if ('lastprotimer' in json && json.lastprotimer.timestamp > Announcer.request.lastprotimer)
    {
        Announcer.request.lastprotimer = json.lastprotimer.timestamp;
        $('#lefttimer').html(json.lastprotimer.left)
        $('#righttimer').html(json.lastprotimer.right)
    }
}

$(document).ready(function(){
    announcer_common_ready();
    Announcer.request = {
        lastclass:  0,
        classcode:  "",
        lastresult: 0,
        lastprotimer: 0
    };
    updateCheck();
});

