

function setResult(rootid, data)
{
    $(rootid+' .class').html(data.class);
    $(rootid+' .champ').html(data.champ);
}

function processData(json)
{
    if ('lastresult' in json && json.lastresult.timestamp > Announcer.request.lastresult)
    {
        Announcer.request.lastresult = json.lastresult.timestamp;
        $('#leftentrant').html(json.lastresult.left.entrant);
        $('#rightentrant').html(json.lastresult.right.entrant);
        setResult('#classresult',  json.lastresult.left)
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
        setResult('#specclass', json.lastclass);
    }

    if ('lastprotimer' in json && json.lastprotimer.timestamp > Announcer.request.lastprotimer)
    {
        Announcer.request.lastprotimer = json.lastprotimer.timestamp;
        $('#lefttimer').html(json.lastprotimer.left)  
        $('#righttimer').html(json.lastprotimer.right)  
    }
}

$(document).ready(function(){
    Announcer.request = {
        lastclass:  0,
        classcode:  "",
        lastresult: 0,
        lastprotimer: 0
    };
    updateCheck();
});

