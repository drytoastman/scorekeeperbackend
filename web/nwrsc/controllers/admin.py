from collections import defaultdict
from datetime import datetime, timedelta
import io
import logging
import operator
import psycopg2
import re
import uuid

from flask import Blueprint, current_app, escape, flash, g, redirect, request, render_template, send_from_directory, session, url_for

from nwrsc.controllers.square import *
from nwrsc.lib.encoding import csv_encode, json_encode
from nwrsc.lib.forms import *
from nwrsc.lib.misc import *
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
    
    if request.endpoint == 'Admin.squareoauth': # special URL without g.series
        return

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
    for res in NumberEntry.allNumbers():
        if Settings.get("superuniquenumbers"):
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
            # We may have changed custom templates, clear the cache now
            current_app.jinja_env.cache.clear()
            return redirect(url_for('.settings'))
        else:
            flashformerrors(form)
    else:
        form.process(obj=Settings.getAll())

    return render_template('/admin/settings.html', form=form)


@Admin.route("/default")
def default():
    if 'resultsheader' in request.args:
        return send_from_directory('templates/results', 'defaultheader.html', mimetype='text/plain')
    elif 'cardtemplate' in request.args:
        return send_from_directory('templates/admin', 'defaultcard.html', mimetype='text/plain')

    raise DisplayableError(header="Unknown request", content="Unknown argument for default")


@Admin.route("/event/<uuid:eventid>/edit", methods=['POST','GET'])
def eventedit():
    """ Process edit event form submission """
    form = EventSettingsForm()
    form.accountid.choices = [(a.accountid, a.name) for a in PaymentAccount.getAllOnline()]
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
    form.accountid.choices = [(a.accountid, a.name) for a in PaymentAccount.getAllOnline()]
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
    """ return the list of new entrants attending each event """
    for e in g.events:
        e.drivers = Attendance.newForEvent(e)
    return render_template('/admin/attendance.html', title='unique attendance', events=g.events)

@Admin.route("/payments")
def payments():
    """ return the list of payments for profiles for an event """
    payments = defaultdict(lambda: defaultdict(list))
    for p in Payment.getAllOnline():
        payments[p.eventid][p.driverid].append(p)
    return render_template('/admin/payments.html', payments=payments, events=g.events)


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


@Admin.route("/event/<uuid:eventid>/cards")
def cards():
    page = request.args.get('page', 'card')
    type = request.args.get('type', 'blank')

    if type == 'blank':
        registered = []
    else:
        registered = Registration.getForEvent(g.eventid)
        for r in registered:
            r.__dict__.update(r.dattr)
            r.__dict__.update(r.cattr)
            r.quickentry = "{:010d}".format(r.carid.time_low)
        if type == 'lastname':
            registered.sort(key=operator.attrgetter('firstname'))
            registered.sort(key=operator.attrgetter('lastname'))
        elif type == 'classnumber':
            registered.sort(key=operator.attrgetter('number'))
            registered.sort(key=operator.attrgetter('classcode'))

    if page == 'csv':
        # CSV data, just use a template and return
        objects = list()
        for r in registered:
            objects.append(dict(r.__dict__))
        titles = ['driverid', 'lastname', 'firstname', 'email', 'address', 'city', 'state', 'zip', 'phone', 'sponsor', 'brag',
                                'carid', 'year', 'make', 'model', 'color', 'number', 'classcode', 'indexcode', 'quickentry']
        return csv_encode("cards", titles, objects)

    elif page == 'template':
        if type == 'blank': registered.append({})
        return render_template('admin/cards.html', registered=registered)

    else:
        from nwrsc.lib.pdfcards import pdfcards
        if type == 'blank': registered.append(None)
        return pdfcards(page, g.event, registered)


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


@Admin.route("/delaccount", methods=['POST'])
def delaccount():
    log.debug("Delete " + request.form['accountid'])
    PaymentAccount.delete(request.form['accountid'])
    return ""

@Admin.route("/accounts", methods=['GET', 'POST'])
def accounts():
    action = request.form.get('submit')
    sqacctform = SquareAccountForm()
    ppacctform = PayPalAccountForm()

    if action == 'Add Square Account':
        if sqacctform.validate():
            p = PaymentAccount()
            p.accountid = sqacctform.accountid.data
            p.name      = sqacctform.name.data 
            p.type      = "square"
            p.attr      = {}
            p.insert()

            s = PaymentAccountSecret()
            s.accountid = sqacctform.accountid.data
            s.secret    = sqacctform.token.data
            s.upsert()
        else:
            flashformerrors(sqacctform)
        return redirect(url_for('.accounts'))

    if action == 'Add PayPal Account':
        if ppacctform.validate():
            p = PaymentAccount()
            p.accountid = ppacctform.accountid.data
            p.name      = ppacctform.name.data 
            p.type      = "paypal"
            p.attr      = { 'something': ppacctform.token.data }
            p.insert()
        else:
            flashformerrors(ppacctform)
        return redirect(url_for('.accounts'))
 
    accounts = PaymentAccount.getAllOnline()
    sqappid = current_app.config.get('SQ_APPLICATION_ID', '')
    return render_template('/admin/paymentaccounts.html', accounts=accounts, sqappid=sqappid, sqacctform=sqacctform, ppacctform=ppacctform)


@Admin.endpoint("Admin.squareoauth")
def squareoauth():
    g.series = request.args.get('state', '')
    if not isSuperAuth() and not isAuth(g.series):
        raise NotLoggedInException()
    with g.db.cursor() as cur:
        cur.execute("SET search_path=%s,'public'; commit; begin", (g.series,))

    square_oauth_account()
    return redirect(url_for('.accounts'))

