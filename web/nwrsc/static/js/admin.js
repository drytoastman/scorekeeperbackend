
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
    return false;
}

