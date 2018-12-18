from webassets import Bundle

def build_js():

    for name, bun in {
        'vendor.js' :      [ jquery, bootstrap, chartjs, fontawesome ],
        'vendor_admin.js': [ flatpickr, datatables, barcode ],
        'admin.js':        [ "js/common.js", "js/admin.js" ],
        'docs.js':         [ "js/common.js" ],
        'register.js':     [ "js/common.js", "js/register.js" ],
        'results.js':      [ "js/common.js" ],
        'announcer.js':    [ "js/commonannouncer.js", "js/announcer.js" ],
        'proannouncer.js': [ "js/commonannouncer.js", "js/proannouncer.js" ]
      }.items():

        globals()[name] = Bundle(*bun, output=name, filters="rjsmin")


    for name, bun in {
        'admin.css':         ["datatables/1.10.16/datatables.css", "flatpickr/4.4.6/flatpickr.css", "scss/admin.scss"],
        'announcer.css':     ["scss/announcer.scss"],
        'announcermini.css': ["scss/announcermini.scss"],
        'docs.css':          ["scss/docs.scss"],
        'register.css':      ["scss/register.scss"],
        'results.css':       ["scss/results.scss"]
      }.items():

        globals()[name] = Bundle(*bun, output=name, filters="libsass", depends="scss/*.scss")


jquery = Bundle(
        "jquery/3.3.1/jquery.js",
        "jquery/3.3.1/sortable-1.12.1.js",
        "jquery/3.3.1/validate-1.17.0.js"
        )

bootstrap   = Bundle("bootstrap/4.1.1/js/bootstrap.bundle.js")
chartjs     = Bundle("chartjs/2.7.2/chart.js")
flatpickr   = Bundle("flatpickr/4.4.6/flatpickr.js")
datatables  = Bundle("datatables/1.10.16/datatables.js")
barcode     = Bundle("barcode/3.9.0/JsBarcode.code128.min.js")
fontawesome = Bundle("font-awesome/5.0.13/font-awesome-svg.js")

build_js()

