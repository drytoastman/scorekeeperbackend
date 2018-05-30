function classView(classcode)
{
    Announcer.request.classcode = classcode;
    Announcer.request.lastclass = 0;
    $('#specclass .class').html("Loading " + classcode);
    $('#specclass .champ').html("");
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
        error:    function(xhr) { if ((xhr.status != 403) && (xhr.statusText != "abort")) { setTimeout(updateCheck, 3000); } }
    });
}

var Announcer = {};

$(document).ready(function(){
    Announcer.mini = (location.search.indexOf('mini=1') >= 0);
    Announcer.base = location.protocol + '//' + location.host + location.pathname;
    Announcer.inflight = null;

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

});
