import logging
import re
import uuid

from flask import abort, g, make_response, render_template, request

from nwrsc.controllers.admin import Admin
from nwrsc.lib.encoding import json_encode
from nwrsc.lib.forms import *
from nwrsc.model import *

log = logging.getLogger(__name__)

@Admin.route("/drivers")
def drivers():
    classdata = ClassData.get()
    carform = CarForm(classdata)
    driverform = DriverForm()
    return render_template('/admin/drivers.html', classdata=classdata, driverform=driverform, carform=carform)

@Admin.route("/getdrivers")
def getdrivers():
    return json_encode(Driver.getAll())

@Admin.route("/getitems")
def getitems():
    ret = dict()
    for did in request.args['driverids'].split(','):
        ret[did] = Car.getForDriver(did)
        for c in ret[did]:
            c.loadActivity()
    return json_encode(ret)

@Admin.route("/usednumbers")
def usednumbers():
    return json_encode(sorted(list(Car.usedNumbers(request.args['driverid'], request.args['classcode'], Settings.get().superuniquenumbers))))

@Admin.route("/deleteitem", methods=['POST'])
def deleteitem():
    try:
        if 'carid' in request.form:
            Car.delete(uuid.UUID(request.form['carid']))
        elif 'driverid' in request.form:
            Driver.delete(uuid.UUID(request.form['driverid']))
        else:
            abort(400, "No carid or driverid given")
    except Exception as e:
        return str(e), 500
    return "";

@Admin.route("/edititem", methods=['POST'])
def edititem():
    form = None
    if 'membership' in request.form:
        form = DriverForm()
        if form.validate():
            d = Driver()
            formIntoAttrBase(form, d)
            d.update()
    elif 'classcode' in request.form:
        classdata = ClassData.get()
        form = CarForm(classdata)
        if form.validate():
            c = Car()
            formIntoAttrBase(form, c)
            c.update()

    if form and len(form.errors) > 0:
        return "\n".join(["{}: {}".format(f, m[0]) for (f, m) in form.errors.items()]), 400
    return ""

@Admin.route("/mergedrivers", methods=['POST'])
def mergedrivers():
    try:
        dest = uuid.UUID(request.form['dest'])
        srcs = [uuid.UUID(x) for x in request.form['src'].split(',')]
        Driver.merge(srcs, dest)
        return ""
    except Exception as e:
        return str(e), 500
    return "";

