from collections import defaultdict
from datetime import datetime, timedelta
import io
import logging
import operator
import psycopg2
import re
import uuid

from flask import abort, Blueprint, current_app, flash, g, redirect, request, render_template, session, url_for

from nwrsc.lib.encoding import json_encode
from nwrsc.lib.forms import *
from nwrsc.model import *

log     = logging.getLogger(__name__)
Admin   = Blueprint("Admin", __name__)
AUTHKEY = 'adminauth'
PATHKEY = 'origpath'

def recordpath():
    if PATHKEY not in session[AUTHKEY]:
        session[AUTHKEY][PATHKEY] = request.path
        session.modified = True

def clearpath():
    if PATHKEY in session[AUTHKEY]:
        del session[AUTHKEY][PATHKEY]
        session.modified = True

@Admin.before_request
def setup():
    """ Every page underneath here requires a password """
    g.title = 'Scorekeeper Admin'
    if AUTHKEY not in session:
        session[AUTHKEY] = {}
    if not g.series in session[AUTHKEY]:
        recordpath()
        return login()

    clearpath()
    g.activeseries = Series.active()
    g.events  = Event.byDate()
    if g.eventid:
        g.event=Event.get(g.eventid)
        if g.event is None:
            abort(404, "No such event")


@Admin.route("/login", methods=['POST', 'GET'])
def login():
    """ Assumes container db is named as such but it works, can't use config/unix socket as it implicitly trusts any user declaration """
    if request.form.get('password'):
        try:
            password = request.form.get('password')[:16].strip()
            psycopg2.connect(host='db', port=5432, user=g.series, password=password, dbname='scorekeeper').close()
            session[AUTHKEY][g.series] = 1
            session.modified = True
            return redirect(session[AUTHKEY][PATHKEY])
        except Exception as e:
            log.error("Login failure: %s", e, exc_info=e)
    return render_template('/admin/login.html')

@Admin.route("/")
def index():
    return render_template('/admin/status.html')

@Admin.route("/event/<uuid:eventid>")
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

@Admin.route("/event/<uuid:eventid>/rungroups")
def rungroups():
    groups = RunGroups.getForEvent(g.eventid)
    #return render_template('/admin/editrungroups.html')
    return render_template('/admin/simple.html', text='This is TBD {}'.format(groups))

@Admin.route("/newseries",  endpoint='newseries')
def newseries():
    return render_template('/admin/simple.html', text='This is TBD')

