// Override/add some core library pieces

String.prototype.format = function() {
    var formatted = this;
    for(var arg in arguments) {
        var val = arguments[arg];
        if (val == undefined) val = "";
        formatted = formatted.replace("{"+arg+"}", val);
    }
    return formatted;
};

if ($.validator) {
    $.validator.addMethod("notinused", function( value, element ) {
        var used = $(element).data("usednumbers") || [];
        return ($.inArray(parseInt(value), used) < 0);
    },  "that number is already in use");
}


// Starting a namespace for our stuff, other things will move here over time
var Scorekeeper = Scorekeeper || {};

Scorekeeper.emailRegex   = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
Scorekeeper.driverFields = ["driverid", "firstname", "lastname", "email", "barcode", "scca", "address", "city", "state", "zip", "phone", "brag", "sponsor", "econtact", "ephone"];

Scorekeeper.add_collapse_icons = function(cid) 
{
    var c = $(cid);
    var i = $("a[href=\""+cid+"\"]");
    c.on('hidden.bs.collapse', function () { i.find('svg').attr('data-icon', 'plus-square'); });
    c.on('shown.bs.collapse',  function () { i.find('svg').attr('data-icon', 'minus-square'); });
};

Scorekeeper.shownavmenu = function(nav, menu)
{
    $(nav).on('shown.bs.collapse', function(){ $(menu).dropdown('toggle'); });
    $(nav).collapse('show');
};


Scorekeeper.load_driver_form = function(form, dr)
{
    for (idx in Scorekeeper.driverFields) {
        var f = Scorekeeper.driverFields[idx];
        form.find('[name='+f+']').val(dr[f]);
    }
    form.find('[name=optoutmail]').prop('checked', dr['optoutmail']);
};



(function ($) {

	var methods = {

        currentclass: function() {
			return gClasses[$(this).find('[name=classcode] option:selected').val()] || {};
        },

		classchange: function() {
            var myform = this;
			var cc = methods.currentclass.call(myform);
			var indexselect = myform.find('[name=indexcode]');

            if (!cc) {
				indexselect.val(0);
			    myform.find('[name=indexcode]').parent().toggle(false);
                return;
            }
            
			if (cc.isindexed) {
				indexselect.toggle(true);
			    myform.find('[name=indexcode]').parent().toggle(true);
				var restrict = cc.idxrestrict;
                if (restrict.length == 0) {
                    restrict = Object.keys(gIndexes);
                }
				
				indexselect.find("option").remove();
                indexselect.append(new Option("", "", false, false));
                restrict.sort();
   				for (var ii = 0; ii < restrict.length; ii++) {
                    indexselect.append(new Option(restrict[ii] + " - " + gIndexes[restrict[ii]], restrict[ii], false, false));
                }
			} else {
				indexselect.val(0);
			    myform.find('[name=indexcode]').parent().toggle(false);
			}
		
            // Clear indexcode and number, they are invalid now
			methods.indexchange.call(myform);
            myform.find('[name=number]').val("");

            // Get the objects we want and set initial values for the structure
            var code = myform.find('[name=classcode] option:selected').val();
            if (!code) return; // blank value with new dialog

            var numobj = myform.find('[name=number]').data('usednumbers', []);
            $("#usedwrapper a").toggle(true);
            $("#usedwrapper span.label").text(" Unavailable Numbers in " + code);
            var ul = $("#usedwrapper ul").html("loading...");
            var driverid = myform.find('[name=driverid]').val(); // only used by admin, register verifies with logged in id

            // Actually make a request for the list and update the UL
            $.get("usednumbers", {'classcode': code, 'driverid': driverid }, function (data) {
                numobj.data('usednumbers', data);
                ul.empty();
                $.each(data, function(ii, num) {
                    ul.append("<li>"+num+"</li>");
                });
            });
		},
	

		indexchange: function() {
            var myform = this;
			var useclsmultcontainer = myform.find('[name=useclsmult]').parent();
			var cc = methods.currentclass.call(myform);
			var ci = myform.find('[name=indexcode] option:selected').val() || "noindex";

			myform.find('[name=useclsmult]').prop('checked', false);
			useclsmultcontainer.toggle(false)

            if (!cc) {
                return;
            } else if (cc.usecarflag && ((cc.multrestrict.length == 0) || ($.inArray(ci, cc.multrestrict) >= 0))) {
				useclsmultcontainer.toggle(true)
			}
		},


		initform: function(car) {
            var myform = this;
			if (!myform.data('cardialoginit'))
			{
				myform.data('cardialoginit', true);
				myform.find('[name=classcode]').change(function() { methods.classchange.call(myform); });
				myform.find('[name=indexcode]').change(function() { methods.indexchange.call(myform); });
                myform.find('[name=number]').after("<div id='usedwrapper'><a data-toggle='collapse' href='#usedlist'><span class='far fa-plus-square'></span><span class='label'></span></a><div id='usedlist' class='collapse'><ul></ul></div></div>");
                Scorekeeper.add_collapse_icons("#usedlist")

				$.validator.setDefaults({ignore:[]});
				myform.validate({
					rules: {
						indexcode: {
							required: function(element) { return (methods.currentclass.call(myform).isindexed); }
						},
                        classcode: {
                            required: true
                        },
						number: {
							required: true,
                            digits: true,
                            notinused: true,
							min: 1,
							max: 1999
						}
					},
			
					messages: { 
						indexcode: 'an index is required for indexed classes',
					},
				});
			}

            $("#usedwrapper a").toggle(false);
            var ul = $("#usedwrapper ul").html("");
			myform.find('[name=driverid]').val(car.driverid || -1);
			myform.find('[name=carid]').val(car.carid || -1);
			myform.find('[name=year]').val(car.year || "");
			myform.find('[name=make]').val(car.make || "");
			myform.find('[name=model]').val(car.model || "");
			myform.find('[name=color]').val(car.color || "");
			myform.find('[name=classcode]').val(car.classcode || "");
			methods.classchange.call(myform);
			myform.find('[name=indexcode]').val(car.indexcode || "");
			methods.indexchange.call(myform);
			myform.find('[name=useclsmult]').prop('checked', car.useclsmult || false);
            myform.find('[name=number]').val(car.number || "");
		}
	};


	$.fn.CarEdit = function( method ) {
		if ( methods[method] ) {
			return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
		} else {
			$.error( 'Method ' +  method + ' does not exist on CarEdit' );
		}    
	};

}) (jQuery);


