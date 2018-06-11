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
    if ((Announcer.inflight != null) && (Announcer.inflight.readyState < 4)) {  // Less than DONE
        console.log("Aborting inflight request");
        Announcer.inflight.abort();
        Announcer.inflight = null;
    }
    console.log("request " + JSON.stringify(Announcer.request));
    Announcer.inflight = $.ajax({
        dataType: "json",
        url:      Announcer.base + 'next',
        data:     Announcer.request,
        success:  function(data) {
            processData(data);
            setTimeout(updateCheck, 1000);
        },
        error:    function(xhr) {
            console.log("check error: " + xhr.statusText);
            if (xhr.statusText == "abort") { return; }
            setTimeout(updateCheck, 3000);
        }
    });
}

function announcer_common_ready()
{
    Announcer = {};
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

}
