
// Make sure namespace is there
var Scorekeeper = Scorekeeper || {};

Scorekeeper.newCountedRow = function(listform, template)
{
    var lastrow = $(listform + ' tr:last');
    var oldcount = lastrow.data('counter');
    var newrow = $(template + ' tr:first').clone();
    var newcount = oldcount+1 || 0;

    newrow.attr('data-counter', newcount);
    newrow.find("input,select").attr("id", function(ix, val) { return val.replace("0", ""+newcount); })
                               .attr("name", function(ix, val) { return val.replace("0", ""+newcount); });
    newrow.find(".deleterow").click(function () { $(this).closest('tr').remove(); return false; });
    newrow.appendTo(listform + ' tbody');
    return newrow;
}


$(document).ready(function() {
    $("input[name=regopened]").flatpickr( { enableTime: true, minuteIncrement: 30 } );
    $("input[name=regclosed]").flatpickr( { enableTime: true, minuteIncrement: 30 } );
	$("input[name=date]").flatpickr( { onChange: function(dateObj, dateStr) {
        d = new Date(dateObj[0]);
        d.setDate(d.getDate() - 2);
        d.setHours(18);
        d.setMinutes(0);
        $("input[name=regclosed]").get(0)._flatpickr.setDate(d);
    }});

    $("input[name=ispro]").change(function() {
        $("input[name=courses]").val(this.checked ? 2 : 1);
    });

    $("select[name=regtype]").change(function() {
        if (this.value != 0) {  // practice/school/etc
            $("input[name=ispractice]").prop("checked", true).prop("disabled", true);
            $("input[name=useastiebreak]").prop("checked", false).prop("disabled", true);
            $("input[name=champrequire]").prop("checked", false).prop("disabled", true);
            $("input[name=ispro]").prop("checked", false).prop("disabled", true);
            $("input[name=isexternal]").prop("checked", false).prop("disabled", true);
        } else {
            $("input[name=ispractice]").prop("disabled", false);
            $("input[name=useastiebreak]").prop("disabled", false);
            $("input[name=champrequire]").prop("disabled", false);
            $("input[name=ispro]").prop("disabled", false);
            $("input[name=isexternal]").prop("disabled", false);
        }
    }).trigger("change");
});
