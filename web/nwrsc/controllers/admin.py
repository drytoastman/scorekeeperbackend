import base64
from collections import defaultdict
from datetime import datetime, date, timedelta
import glob
import io
import json
import logging
import operator
import os
import psycopg2
import re
import subprocess
import uuid

from flask import current_app, escape, flash, g, Markup, redirect, request, render_template, render_template_string, Response, send_from_directory, session, url_for
from werkzeug import secure_filename

from nwrsc.controllers.blueprints import *
from nwrsc.lib.encoding import csv_encode, json_encode, time_print 
from nwrsc.lib.forms import *
from nwrsc.lib.misc import *
from nwrsc.model import *
from nwrsc.model.superauth import SuperAuth

log      = logging.getLogger(__name__)
ADMINKEY = 'admin'
AUTHKEY  = 'auth'
SUPERKEY = 'authSuper'

# Keep all session access in one place for easy browsing/control

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
    outsideendpoints = ('Admin.squareoauth')
    authendpoints = ('Admin.login', 'Admin.slogin')
    mainserverendpoints = ('Admin.drivers', 'Admin.purge', 'Admin.archive')

    log.warning("session is {}".format(session))
    if request.endpoint in outsideendpoints: # special URL without g.series
        return

    if not g.series:
        return baseindex()

    if g.seriestype != Series.ACTIVE:
        raise ArchivedSeriesException()

    g.mainserver = current_app.config['IS_MAIN_SERVER']
    if not g.mainserver and request.endpoint in mainserverendpoints:
        return "This is not available off of the main server"

    g.superauth = isSuperAuth()
    try:
        token = current_app.usts.loads(request.args['token'], max_age=86400) # 1 day token expiry
        if token['superauth']:
            g.superauth = True
    except:
        pass

    if not g.superauth and not isAuth(g.series) and request.endpoint not in authendpoints:
        recordPath(ADMINKEY)
        return login()

    if request.endpoint not in authendpoints:
        clearPath(ADMINKEY)

    g.doweekendmembers = Settings.get("doweekendmembers")
    g.settings = Settings.getAll()
    g.events = Event.byDate()
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
            return redirect(getRecordedPath(ADMINKEY, url_for(".index")))
        flash("Incorrect password")
        log.error("SuperAdmin login failure")
    return render_template('/admin/login.html', base='.slogin', form=form, series='SuperAdmin')


@Admin.route("/login", methods=['POST', 'GET'])
def login():
    form = SeriesPasswordForm()
    if form.validate_on_submit():
        try:
            Series.testPassword(password=form.password.data.strip())
            authSeries(g.series)
            return redirect(getRecordedPath(ADMINKEY, url_for(".index")))
        except InvalidPasswordException as ip:
            log.error("Login failure for {}: {}".format(g.series, ip))
        except Exception as e:
            log.error("Login failure for {}: {}".format(g.series, ip), exc_info=e)
    return render_template('/admin/login.html', base='.login', form=form, series=g.series)


@Admin.endpoint("Admin.base")
def baseindex():
    return render_template('/admin/allstatus.html', events=Event.allSeriesByDate())

@Admin.route("/")
def index():
    for e in g.events:
        e.registration = Registration.getForEvent(e.eventid, e.paymentRequired())
    return render_template('/admin/status.html', today=datetime.date.today())

@Admin.route("/event/<uuid:eventid>/")
def event():
    exform = None
    if g.event.isexternal:
        exform = ExternalResultForm(Driver.getAllForSeries(), ClassData.get())
    return render_template('/admin/event.html', event=g.event, exform=exform)

@Admin.route("/event/<uuid:eventid>/externalresults")
def externalresults():
    return json_encode(ExternalResult.getAll(g.event.eventid))

@Admin.route("/event/<uuid:eventid>/newexternal", methods=['POST'])
def newexternal():
    exform = ExternalResultForm(Driver.getAllForSeries(), ClassData.get())
    if exform.validate():
        try:
            res = ExternalResult()
            formIntoAttrBase(exform, res)
            res.eventid = g.event.eventid
            res.insert()
        except Exception as e:
            flash("Exception inserting result: {}".format(e))
            log.error("Exception insert result: {}", exc_info=e)
    else:
        flashformerrors(exform)

    return redirect(url_for('.event'))

#@Admin.route("/event/<uuid:eventid>/externaltext", methods=['POST'])
def externaltext():
    tokens  = request.form.get('data').split()
    isfloat = re.compile('\d+\.\d+')
    entries = list()
    ii      = 6
    drivers = {(d.firstname,d.lastname):d for d in Driver.getAllForSeries()}
    classdata = ClassData.get()
    indexrev  = {i.value:i.indexcode for i in classdata.indexlist.values()}

    while ii < len(tokens):
        if isfloat.search(tokens[ii-2]) and isfloat.search(tokens[ii-1]) and isfloat.search(tokens[ii]):
            name = (tokens[ii-6], tokens[ii-5])
            if name in drivers:
                d = drivers[name]
                extclass = tokens[ii-4]
                try:
                    idxclass = indexrev[float(tokens[ii-1])]
                except:
                    idxclass = 'N/A'

                for code in classdata.classlist:
                    if extclass == code:
                        d.classcode = code
                        break
                    elif extclass in classdata.restrictedRegistrationIndexes(code):
                        d.classcode = code
                        break
                    elif idxclass in classdata.restrictedRegistrationIndexes(code):
                        d.classcode = code
                        break

                d.extclass = tokens[ii-4]
                d.raw = tokens[ii-2]
                d.index = tokens[ii-1]
                d.net = tokens[ii]
                entries.append(d)
            ii = ii + 6
        else:
            ii = ii + 1

    return json_encode(entries)

@Admin.route("/event/<uuid:eventid>/delexternal", methods=['POST'])
def delexternal():
    try:
        ExternalResult(eventid = uuid.UUID(request.form.get('eventid', None)),
                     driverid  = uuid.UUID(request.form.get('driverid', None)),
                     classcode = request.form.get('classcode', None)).delete()
    except Exception as e:
        log.exception("delete failed")
        return "delete failed", 403
    return ""



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
    g.classdata = ClassData.get()
    ClassListForm.setIndexes(g.classdata.indexlist) # global variable danger, but no way around it with current WTForms

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
        g.classdata = ClassData.get()
        g.classdata.classlist.pop('HOLD', None)
        for key, cls in sorted(g.classdata.classlist.items()):
            form.classlist.append_entry(cls)

    empty = ClassListForm()
    empty.classlist.append_entry(Class.empty())
    return render_template('/admin/classlist.html', form=form, empty=empty)


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

    empty = IndexListForm()
    empty.indexlist.append_entry(Index.empty())
    lists = sorted([os.path.basename(s[:-5]) for s in glob.glob(os.path.join(current_app.root_path, 'static/indexlists/*.json'))])
    return render_template('/admin/indexlist.html', form=form, empty=empty, lists=lists)


@Admin.route("/indexreset")
def indexreset():
    try:
        index = request.args.get('index', 'none')
        prefix = index.replace('_', ' ')
        with open(os.path.join(current_app.root_path, 'static/indexlists', '{}.json'.format(index))) as fp:
            indexes = json.load(fp)
            active = Index.activeIndexes()
            for missing in set(active) - set(indexes):
                indexes[missing] = 1.234  # filler index for things that are missing
            ClassData.get().updateIndexesTo({k:Index(indexcode=k, value=v, descrip='{} {}'.format(prefix, k)) for k,v in indexes.items()})
    except Exception as e:
        flash("Exception loading indexes from file: {}".format(e))

    return redirect(url_for('.indexlist'))


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


@Admin.route("/password", methods=['POST', 'GET'])
def password():
    form = ChangePasswordForm()
    if request.form:
        try:
            if form.validate():
                Series.changePassword(host=current_app.config['DBHOST'], port=current_app.config['DBPORT'], oldpassword=form.oldpassword.data, newpassword=form.newpassword.data)
                return redirect(url_for('.index'))
            else:
                flashformerrors(form)
        except Exception as e:
            flash("Unable to change password: {}".format(e))
    return render_template('/admin/password.html', form=form)


@Admin.route("/default")
def default():
    if 'resultsheader' in request.args:
        return send_from_directory('templates/results', 'defaultheader.html', mimetype='text/plain')
    elif 'cardtemplate' in request.args:
        return send_from_directory('templates/admin', 'defaultcard.html', mimetype='text/plain')
    elif 'cards' in request.args:
        return send_from_directory('templates/admin', 'cards.html', mimetype='text/plain')

    raise DisplayableError(header="Unknown request", content="Unknown argument for default")


@Admin.route("/allevents", methods=['POST','GET'])
def allevents():
    return render_template('/admin/allevents.html')

@Admin.route("/eventlist")
def eventlist():
    events = Event.byDate()
    for e in events:
        e.status = not e.hasOpened() and 'Not Yet Open' or e.isOpen()  and 'Open' or 'Closed'
        e.date = { 'display': e.date.strftime("%a %b %d"), 'sort': datetime.datetime.combine(e.date, datetime.time(0)).timestamp() }
        e.regopened = { 'display': e.regopened.strftime("%a %b %d %H:%S"), 'sort': e.regopened.timestamp() }
        e.regclosed = { 'display': e.regclosed.strftime("%a %b %d %H:%S"), 'sort': e.regclosed.timestamp() }
        e.regcount = e.getRegisteredCount()
        account = PaymentAccount.get(e.accountid)
        if account:
            e.account = account.name
    return json_encode(events)


@Admin.route("/event/<uuid:eventid>/edit", methods=['POST','GET'])
def eventedit():
    """ Process edit event form submission """
    form = EventSettingsForm(Event.REGTYPES, [(a.accountid, a.name) for a in PaymentAccount.getAll()])
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
    form = EventSettingsForm(Event.REGTYPES, [(a.accountid, a.name) for a in PaymentAccount.getAll()])
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


@Admin.route("/createmultipleevents", methods=['POST','GET'])
def createmultipleevents():
    """ Present form to create a series of events from a template """
    form = MultipleEventsForm(Event.REGTYPES, [(a.accountid, a.name) for a in PaymentAccount.getAll()])
    if request.form:
        if form.validate():
            tz = pytz.timezone(current_app.config['UI_TIME_ZONE'])
            def toutc(dt): # have to do this here, not in forms as we are splicing things together
                return tz.localize(dt).astimezone(datetime.timezone.utc)

            template = Event.new()
            formIntoAttrBase(form, template)
            for k in ('namedates', 'closeday', 'closetime', 'opendays'):
                del template.attr[k]

            for name,date in form.namedates:
                eventdow = date.data.isoweekday()
                closedow = int(form.closeday.data)
                closedelta = eventdow - closedow
                if closedelta <= 0:
                    closedelta += 7

                template.eventid = uuid.uuid1()
                template.name = name.data
                template.date = date.data
                template.regopened = toutc(datetime.datetime.combine(template.date - timedelta(days=form.opendays.data), datetime.time()))
                template.regclosed = toutc(datetime.datetime.combine(template.date - timedelta(days=closedelta), form.closetime.data.time()))
                template.insert()
            return redirect(url_for('.index'))
        else:
            flashformerrors(form)
    else:
        attrBaseIntoForm(Event.new(), form)

    empty = MultipleEventsForm(Event.REGTYPES, [(a.accountid, a.name) for a in PaymentAccount.getAll()])
    empty.namedates.append_entry({})
    return render_template('/admin/multipleevents.html', form=form, empty=empty, url=url_for('.createmultipleevents'))


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
    return render_template('/admin/attendance.html', title='Unique Attendance', events=g.events)


@Admin.route("/contactlist")
def contactlist():
    return render_template('/admin/contactlist.html', events=g.events)

@Admin.route("/activitylist")
def activitylist():
    ret = list(Attendance.getActivity().values())
    unsub = Unsubscribe.getUnsub(Settings.get('emaillistid'))
    for e in ret:
        if e.optoutmail or e.driverid in unsub:
            e.email = '********'
    return json_encode(ret)


@Admin.route("/ustsdecode")
def ustsdecode():
    return json_encode(current_app.usts.loads(request.args['token']))


@Admin.route("/emailtool", methods=['GET','POST'])
def emailtool():
    form = GroupEmailForm()
    upfl = current_app.config.get('UPLOAD_FOLDER', '')
    uppr = os.path.isdir(upfl)

    if 'emaillist' in request.form:
        emaillist = json.loads(request.form['emaillist'])
        form.token.data = current_app.usts.dumps(emaillist)
        form.count.data = len(emaillist)
        form.unsub.data = True
    elif 'token' in request.form:
        try:
            if form.validate_on_submit():
                attachments = []
                listid = Settings.get('emaillistid')
                for d in (form.attach1.data, form.attach2.data):
                    if d and d.filename:
                        sfilename = secure_filename(d.filename)
                        d.save(os.path.join(upfl, sfilename))
                        attachments.append({'name': sfilename, 'mime': d.mimetype})

                if form.unsub.data:
                    form.body.data += "\n<p>&nbsp;</p><hr><p>Unsubscribe at {{url}}</p>"

                for r in current_app.usts.loads(request.form['token'], max_age=86400):
                    unsub = {}
                    if form.unsub.data and r.get('driverid', ''):
                        utoken = current_app.usts.dumps({'id': r['driverid'], 'listid': listid})
                        unsub['url']    = url_for('Register.unsubscribe', series=g.series, token=utoken, _external=True)
                        unsub['listid'] = listid

                    EmailQueue.queueMessage(
                        subject     = form.subject.data,
                        recipient   = r,
                        replyto     = { 'name': form.replyname.data, 'email': form.replyemail.data },
                        body        = render_template_string(form.body.data, url=unsub['url'], **r),
                        unsub       = unsub,
                        attachments = attachments,
                    )

                flash("Group mail queued", category='success')
                return redirect(url_for('.contactlist'))

        except Exception as e:
            flash("Group mail error: {}".format(e))
            log.exception(e)

    return render_template('/admin/emailtool.html', form=form, attachments=uppr, sender=os.environ['MAIL_SEND_FROM'])



@Admin.route("/weekendreport")
def weekendreport():
    weekends = set()
    for e in g.events:
        iso = e.date.isocalendar()
        start = e.date + datetime.timedelta(days=6-iso[2]) # Sat
        end   = e.date + datetime.timedelta(days=7-iso[2]) # Sun
        weekends.add((start ,end))
    return render_template('/admin/weekendreport.html', weekends=weekends)

@Admin.route("/weekendlist")
def weekendlist():
   return json_encode(WeekendMembers.getAll())


@Admin.route("/event/<uuid:eventid>/entryadmin")
def entryadmin():
    return render_template('/admin/entryadmin.html', event=g.event)

@Admin.route("/event/<uuid:eventid>/registered")
def registered():
    ret = Registration.getForEvent(g.eventid)
    unsub = Unsubscribe.getUnsub(Settings.get('emaillistid'))
    for r in ret:
        if r.optoutmail or r.driverid in unsub:
            r.email = '********'
        r.regmodified = time_print(r.regmodified, '%m-%d %H:%M')
        r.cdesc = ' '.join(filter(None, [r.cattr.get(k, None) for k in ('year', 'make', 'model', 'color')]))
    return json_encode(list(ret))


@Admin.route("/event/<uuid:eventid>/delreg", methods=['POST'])
def delreg():
    carid = uuid.UUID(request.form.get('carid', None))
    if not Registration.deleteById(g.eventid, carid):
        return "Delete Failed", 403
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
    for e in Registration.getForEvent(g.eventid, g.event.paymentRequired()):
        groups.put(e)
    return render_template('/admin/editrungroups.html', groups=groups)


@Admin.route("/event/<uuid:eventid>/cards")
def cards():
    page = request.args.get('page', 'card')
    ctype = request.args.get('type', 'blank')

    if ctype == 'blank':
        registered = []
    else:
        registered = Registration.getForEvent(g.eventid, g.event.paymentRequired())
        for r in registered:
            r.__dict__.update(r.dattr)
            r.__dict__.update(r.cattr)
            q = "{:010d}".format(r.carid.time_low)
            r.quickentry = "{} {} {}".format(q[0:3], q[3:6], q[6:])
            r.caridbarcode = r.carid and "{:040d}".format(r.carid.int) or "" # UUID in base 10 with extra zeros to make 40 digits which fits into 128C
        if ctype == 'lastname':
            registered.sort(key=lambda m: getattr(m, 'firstname').lower())
            registered.sort(key=lambda m: getattr(m, 'lastname').lower())
        elif ctype == 'classnumber':
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
        if ctype == 'blank': registered.append({})
        return render_template('admin/cards.html', registered=registered)

    elif page == 'html2pdf':
        url = "http://127.0.0.1{}".format(url_for('.cards', type=ctype, page='template', token=current_app.usts.dumps({'superauth': 1})))
        cmd = ["wkhtmltopdf", "--disable-smart-shrinking", "--zoom", "0.90", "--page-height", "5in", "--page-width", "8in", url, "-"]
        def generate_pdf():
            log.info("Running %s", cmd)
            yield subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
        return Response(generate_pdf(), mimetype='application/pdf')


@Admin.route("/newseries", methods=['GET', 'POST'])
def newseries():
    form = SeriesForm()
    if form.validate_on_submit():
        try:
            series = form.name.data.lower()
            Series.copySeries(host=current_app.config['DBHOST'], port=current_app.config['DBPORT'], series=series,
                              password=form.password.data, csettings=form.copysettings.data, cclasses=form.copyclasses.data, caccounts=form.copyaccounts.data, ccars=form.copycars.data)
            authSeries(series)
            return redirect(url_for('.settings', series=series))
        except Exception as e:
            flash("Error creating series: {}".format(e))
            log.warning(e)
    else:
        try:
            m = re.search("(.*)(\d{4})", g.series)
            form.name.data = m.group(1) + str((date.today()+ timedelta(days=90)).year)
        except:
            form.name.data = g.series + "_next"
        form.copysettings.data = True
        form.copyclasses.data = True
        form.copyaccounts.data = True
    return render_template('/admin/newseries.html', form=form)


@Admin.route("/purge", methods=['GET', 'POST'])
def purge():
    thisyear = date.today().year
    lastyear = thisyear - 7
    if request.form:
        count = 0
        if 'purgeclass' in request.form:
            data = dict(request.form)
            data.pop('purgeclass', None)
            count = Car.deleteByClass(tuple(data.keys()))

        elif 'purgeyear' in request.form:
            untilyear = int(request.form.get('year', lastyear))
            for carid, activity in Series.getCarActivity(untilyear).items():
                if activity.year < untilyear:
                    try:  # Use constraints to stop us from deleteing in use cars
                        count += Car.deleteById(carid)
                    except Exception as e:
                        g.db.rollback() 
                        log.info("Not deleting car {}: {}".format(carid, e))

        flash("Deleted {} cars".format(count))
        return redirect(url_for('.purge'))

    classdata = ClassData.get()
    return render_template('/admin/purge.html', superauth=g.superauth, classdata=classdata, years=range(thisyear, lastyear, -1))


@Admin.route("/purgedriver", methods=['POST'])
def purgedriver():
    if not g.superauth:
        flash("Driver purge is only available with SuperAuth")
        return redirect(url_for('.purge'))

    untilyear = int(request.form.get('year', date.today().year - 7))
    count = 0
    for driverid, activity in Series.getDriverActivity(untilyear).items():
        if activity.year < untilyear:
            try:  # Use constraints to stop us from deleteing in use drivers
                count += SuperAuth.deleteDriver(driverid)
            except Exception as e:
                g.db.rollback() 
                log.info("Not deleting driver {}: {}".format(driverid, e))
    flash("Deleted {} drivers".format(count))
    return redirect(url_for('.purge'))

@Admin.route("/decodetoken")
def decodetoken():
    if not g.superauth:
        return "decode is only available via superauth"
    try:
        base64d, timestamp = current_app.usts.make_signer(None).unsign(request.args['token'], return_timestamp=True)
        payload = current_app.usts.load_payload(base64d)
        return "payload ({}, {})".format(timestamp, payload)
    except Exception as e:
        return "Exception {}: {}".format(e.__class__.__name__, e)
