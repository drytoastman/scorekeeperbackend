from collections import defaultdict
from datetime import datetime, timedelta
import io
import logging
import operator
import psycopg2
import re
import uuid

from flask import Blueprint, current_app, flash, g, redirect, request, render_template, session, url_for

from nwrsc.lib.encoding import json_encode
from nwrsc.lib.forms import *
from nwrsc.lib.misc import InvalidEventException
from nwrsc.model import *

log      = logging.getLogger(__name__)
Admin    = Blueprint("Admin", __name__)
ADMINKEY = 'admin'
AUTHKEY  = 'auth'
SUPERKEY = 'authSuper'
PATHKEY  = 'origpath'

# Keep all session access in one place for easy browsing/control

def recordPath():
    if ADMINKEY not in session:
        session[ADMINKEY] = {}
    if PATHKEY not in session[ADMINKEY]:
        session[ADMINKEY][PATHKEY] = request.path
        session.modified = True

def clearPath():
    if ADMINKEY not in session:
        session[ADMINKEY] = {}
    if PATHKEY in session[ADMINKEY]:
        del session[ADMINKEY][PATHKEY]
        session.modified = True

def getRecordedPath():
    if ADMINKEY not in session or PATHKEY not in session[ADMINKEY]:
        return url_for(".index")
    return session[ADMINKEY][PATHKEY]

def authSeries(series):
    if ADMINKEY not in session:
        session[ADMINKEY] = {}
    if AUTHKEY not in session[ADMINKEY]:
        session[ADMINKEY][AUTHKEY] = {}
    session[ADMINKEY][AUTHKEY][series] = 1
    session.modified = 1

def isAuth(series):
    if ADMINKEY not in session: return False
    if AUTHKEY not in session[ADMINKEY]: return False
    return g.series in session[ADMINKEY][AUTHKEY]

def authSuper():
    if ADMINKEY not in session:
        session[ADMINKEY] = {}
    session[ADMINKEY][SUPERKEY] = 1
    session.modified = 1

def isSuperAuth():
    if ADMINKEY not in session: return False
    return SUPERKEY in session[ADMINKEY]


@Admin.before_request
def setup():
    """ Every page underneath here requires a password """
    g.title = 'Scorekeeper Admin'
    g.activeseries = Series.active()
    if not g.series:
        return render_template('/admin/bluebase.html')

    g.superauth = isSuperAuth()
    if not g.superauth and not isAuth(g.series):
        recordPath()
        return login()

    clearPath()
    g.events  = Event.byDate()
    if g.eventid:
        g.event=Event.get(g.eventid)
        if g.event is None:
            raise InvalidEventException()


@Admin.route("/slogin", methods=['POST', 'GET'])
def slogin():
    form = SeriesPasswordForm()
    spw = current_app.config['SUPER_ADMIN_PASSWORD']
    if not spw:
        flash("SuperAdmin password is not enabled")
        return render_template("admin/simple.html")

    if form.validate_on_submit():
        if spw == form.password.data.strip():
            authSuper()
            return redirect(getRecordedPath())
        flash("Incorrect password")
    return render_template('/admin/login.html', base='.slogin', form=form, series='SuperAdmin')


@Admin.route("/login", methods=['POST', 'GET'])
def login():
    form = SeriesPasswordForm()
    if form.validate_on_submit():
        try:
            AttrBase.testPassword(user=g.series, password=form.password.data.strip())
            authSeries(g.series)
            return redirect(getRecordedPath())
        except Exception as e:
            log.error("Login failure: %s", e, exc_info=e)
    return render_template('/admin/login.html', base='.login', form=form, series=g.series)


@Admin.endpoint("Admin.base")
@Admin.route("/")
def index():
    return render_template('/admin/status.html')

@Admin.route("/event/<uuid:eventid>/")
def event():
    return render_template('/admin/event.html', event=g.event)

@Admin.route("/numbers")
def numbers():
    numbers = defaultdict(lambda: defaultdict(set))
    settings = Settings.get()
    for res in NumberEntry.allNumbers():
        if settings.superuniquenumbers:
            res.code = "All"
        numbers[res.classcode][res.number].add(res.firstname+" "+res.lastname)
    return render_template('/admin/numberlist.html', numbers=numbers)

@Admin.route("/printhelp")
def printhelp():
    return render_template("/admin/printhelp.html")

@Admin.route("/restricthelp")
def restricthelp():
    return render_template('/admin/restricthelp.html')


@Admin.route("/classlist", methods=['POST', 'GET'])
def classlist():
    classdata = ClassData.get()
    ClassListForm.setIndexes(classdata.indexlist)
    form = ClassListForm()
    if request.form:
        if form.validate():
            try:
                ClassData.get().updateClassesTo({k.data['classcode']:Class.fromForm(k.data) for k in form.classlist})
                return redirect(url_for('.classlist'))
            except psycopg2.IntegrityError as ie:
                flash("Unable to update classes: {}".format(ie))
            except Exception as e:
                flash("Exception processing classlist: {}".format(e))
                log.error("General exception processing classlist", exc_info=e)
        else:
            flashformerrors(form)
    else:
        classdata = ClassData.get()
        classdata.classlist.pop('HOLD', None)
        for key, cls in sorted(classdata.classlist.items()):
            form.classlist.append_entry(cls)

    return render_template('/admin/classlist.html', form=form)


@Admin.route("/indexlist", methods=['POST', 'GET'])
def indexlist():
    form = IndexListForm()
    if request.form:
        if form.validate():
            try:
                ClassData.get().updateIndexesTo({k.data['indexcode']:Index.fromForm(k.data) for k in form.indexlist})
                return redirect(url_for('.indexlist'))
            except psycopg2.IntegrityError as ie:
                flash("Unable to update indexes: {}".format(ie))
            except Exception as e:
                flash("Exception processing indexlist: {}".format(e))
                log.error("General exception processing indexlist", exc_info=e)
        else:
            flashformerrors(form)
    else:
        classdata = ClassData.get()
        classdata.indexlist.pop("", None)
        for key, idx in sorted(classdata.indexlist.items()):
            form.indexlist.append_entry(idx)

    return render_template('/admin/indexlist.html', form=form)


@Admin.route("/settings", methods=['POST', 'GET'])
def settings():
    form = SettingsForm()
    if request.form:
        if form.validate():
            newsettings = Settings.fromForm(form)
            newsettings.save()
            return redirect(url_for('.settings'))
        else:
            flashformerrors(form)
    else:
        form.process(obj=Settings.get())

    return render_template('/admin/settings.html', settings=settings, form=form)


@Admin.route("/event/<uuid:eventid>/edit", methods=['POST','GET'])
def eventedit():
    """ Process edit event form submission """
    form = EventSettingsForm()
    if request.form:
        if form.validate():
            newevent = Event()
            formIntoAttrBase(form, newevent)
            newevent.update()
            return redirect(url_for('.eventedit'))
        else:
            flashformerrors(form)
    else:
        attrBaseIntoForm(g.event, form)

    return render_template('/admin/eventedit.html', form=form, url=url_for('.eventedit'))


@Admin.route("/createevent", methods=['POST','GET'])
def createevent():
    """ Present form to create a new event """
    form = EventSettingsForm()
    if request.form:
        if form.validate():
            newevent = Event()
            formIntoAttrBase(form, newevent)
            newevent.insert()
            return redirect(url_for('.index'))
        else:
            flashformerrors(form)
    else:
        attrBaseIntoForm(Event.new(), form)

    return render_template('/admin/eventedit.html', form=form, url=url_for('.createevent'))


@Admin.route("/event/<uuid:eventid>/deleteevent")
def deleteevent():
    """ Request to delete an event, verify if we can first, then do it """
    try:
        g.event.delete()
        return redirect(url_for(".index"))
    except psycopg2.IntegrityError as ie:
        flash("Unable to delete event as its still referenced: {}".format(ie.diag.message_detail))
        return redirect(url_for(".event"))


@Admin.route("/archive", methods=['GET', 'POST'])
def archive():
    """ Request to archive the series, make sure all results/settings are in the results table and then delete the series """
    form = ArchiveForm()
    if form.validate_on_submit():
        try:
            if form.name.data == g.series:
                Result.cacheAll()
                g.db.close() # Need to drop the localuser connection before delete or we get deadlock
                del g.db
                Series.deleteSeries(host=current_app.config['DBHOST'], port=current_app.config['DBPORT'])
                return redirect(url_for(".base", series=None))
            flash("Incorrect series name")
        except Exception as e:
            flash("Unable to delete series: {}".format(e))

    return render_template("/admin/archive.html", form=form)


@Admin.route("/seriesattend")
def seriesattend():
    """ Return the list of fees paid before this event """
    e = Event()
    e.name = "All Events"
    e.drivers = Attendance.getAll()
    return render_template('/admin/attendance.html', title='Series Attendance', events=[e])

@Admin.route("/eventattend")
def eventattend():
    """ Return the list of entrants attending each event """
    for e in g.events:
        e.drivers = Attendance.forEvent(e)
    return render_template('/admin/attendance.html', title='Event Attendance', events=g.events)

@Admin.route("/uniqueattend")
def uniqueattend():
    """ Return the list of new entrantsa attending each event """
    for e in g.events:
        e.drivers = Attendance.newForEvent(e)
    return render_template('/admin/attendance.html', title='Unique Attendance', events=g.events)


@Admin.route("/contactlist")
def contactlist():
    return render_template('/admin/contactlist.html', events=g.events)

@Admin.route("/activitylist")
def activitylist():
    activity = Attendance.getActivity()
    return json_encode(list(activity.values()))


@Admin.route("/event/<uuid:eventid>/entryadmin")
def entryadmin():
    return render_template('/admin/entryadmin.html', event=g.event)

@Admin.route("/event/<uuid:eventid>/registered")
def registered():
    ret = Registration.getForEvent(g.eventid)
    for r in ret:
        r.cdesc = ' '.join(filter(None, [r.cattr.get(k, None) for k in ('year', 'make', 'model', 'color')]))
    return json_encode(ret)

@Admin.route("/event/<uuid:eventid>/delreg", methods=['POST'])
def delreg():
    carid = uuid.UUID(request.form.get('carid', None))
    Registration.delete(g.eventid, carid)
    return ""

@Admin.route("/event/<uuid:eventid>/rungroups", methods=['GET', 'POST'])
def rungroups():
    if request.form:
        try:
            newgroups = defaultdict(list)
            for key, val in request.form.items():
                if val.strip():
                    newgroups[int(key[5:])] = val.split(',')
            RunGroups.getForEvent(g.eventid).update(g.eventid, newgroups)
        except Exception as e:
            flash(str(e))
        return redirect(url_for('.rungroups'))
    groups = RunGroups.getForEvent(g.eventid)
    for e in Registration.getForEvent(g.eventid):
        groups.put(e)
    return render_template('/admin/editrungroups.html', groups=groups)

@Admin.route("/newseries", methods=['GET', 'POST'])
def newseries():
    form = SeriesForm()
    if form.validate_on_submit():
        try:
            series = form.name.data.lower()
            Series.copySeries(host=current_app.config['DBHOST'], port=current_app.config['DBPORT'], series=series,
                              password=form.password.data, csettings=form.copysettings.data, cclasses=form.copyclasses.data, ccars=form.copycars.data)
            authSeries(series)
            return redirect(url_for('.settings', series=series))
        except Exception as e:
            flash("Error creating series: {}".format(e))
            log.warning(e)
    else:
        form.name.data = g.series
        form.copysettings.data = True
    return render_template('/admin/newseries.html', form=form)

