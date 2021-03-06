from collections import defaultdict
import datetime
import itertools
import logging
import os
import socket
import time
import uuid

import itsdangerous
from flask import abort, current_app, flash, g, get_template_attribute, redirect, request, render_template, Response, session, stream_with_context, url_for
from werkzeug.exceptions import BadRequestKeyError

from .blueprints import *
from ..model import *
from ..lib.forms import *
from ..lib.misc import *
from ..lib.encoding import json_encode, ical_encode

log = logging.getLogger(__name__)


REGISTERKEY='register'

@Register.before_request
def setup():
    g.title = 'Scorekeeper Registration'
    g.isonsite = current_app.config['ONSITE']
    g.activeseries = Series.active()
    g.selection = request.endpoint
    if 'driverid' in session:
        g.driver = Driver.get(session['driverid'])
    else:
        g.driver = None

    if g.series:
        if g.seriestype != Series.ACTIVE:
            raise ArchivedSeriesException()
        g.settings = Settings.getAll()
        g.classdata = ClassData.get()

    openendpoints = ('Register.view', 'Register.ical', 'Register.login', 'Register.emailsent', 'Register.finish', 'Register.reset', 'Register.unsubscribe')
    excendpoints  = ('Register.eventspost', 'Register.usednumbers', 'Register.payment', 'Register.paypalexecute', 'Register.squarepaymentcomplete')

    if not g.driver and request.endpoint not in openendpoints:
        if request.endpoint in excendpoints:
            raise NotLoggedInException()
        recordPath(REGISTERKEY)
        return login()

    if request.endpoint not in openendpoints:
        clearPath(REGISTERKEY)


####################################################################
# Authenticated functions

@Register.route("/")
def index():
    g.selection = 'Register.events'
    return render_template('register/bluebase.html')

@Register.route("/<series>/")
def series():
    """ If logged in, just redirect to events """
    return redirect(url_for('.events'))


@Register.route("/profile")
@Register.route("/<series>/profile")
def profile():
    profileform  = DriverForm(prefix='driver')
    upcoming     = getAllUpcoming(g.driver.driverid)
    attrBaseIntoForm(g.driver, profileform)

    listids  = Series.emailListIds()
    unsubids = set(Unsubscribe.get(g.driver.driverid))

    passwordform = PasswordChangeForm(prefix='password')
    passwordform.driverid.data = g.driver.driverid

    askprofile = any2bool(request.args.get('askprofile'))

    return render_template('register/profile.html', listids=listids, unsubids=unsubids, profileform=profileform, passwordform=passwordform, upcoming=upcoming, surpressmenu=True, askprofile=askprofile)


@Register.route("/profilepost", methods=['POST'])
@Register.route("/<series>/profilepost", methods=['POST'])
def profilepost():
    form = DriverForm(prefix='driver')
    if form.validate_on_submit():
        formIntoAttrBase(form, g.driver)
        g.driver.update()
    flashformerrors(form)
    return redirect(url_for('.profile'))


@Register.route("/passwordupdate ", methods=['POST'])
@Register.route("/<series>/passwordupdate", methods=['POST'])
def passwordupdate():
    form = PasswordChangeForm(prefix='password')
    if form.validate_on_submit():
        if current_app.hasher.check_password_hash(g.driver.password, form.oldpassword.data):
            Driver.updatepassword(g.driver.driverid, g.driver.username, form.newpassword.data)
        else:
            flash("Incorrect current password")
    flashformerrors(form)
    return redirect(url_for('.profile'))


@Register.route("/<series>/subunsub", methods=['POST'])
@Register.route("/subunsub", methods=['POST'])
def subunsub():
    subids = set(request.form.keys())
    allids = Series.emailListIds()
    for k in subids & allids:
        Unsubscribe.clear(g.driver.driverid, k)
    for k in allids - subids:
        Unsubscribe.set(g.driver.driverid, k)
    return redirect(url_for('.profile'))


@Register.route("/<series>/cars")
def cars():
    carform = CarForm(g.classdata)
    events  = {e.eventid:e for e in Event.byDate(ignoreexternal=True)}
    cars    = {c.carid:c   for c in Car.getForDriver(g.driver.driverid)}
    active  = defaultdict(set)
    for carid,eventid in Driver.activecars(g.driver.driverid):
        active[carid].add(eventid)
    return render_template('register/cars.html', events=events, cars=cars, active=active, carform=carform)


@Register.route("/<series>/carspost", methods=['POST'])
def carspost():
    carform = CarForm(g.classdata)

    try:
        action = request.form.get('submit')
        if action == 'Delete':
            Car.deleteWCheck(request.form.get('carid', ''), g.driver.driverid)
        elif carform.validate():
            car = Car()
            formIntoAttrBase(carform, car)
            if action == 'Update':
                car.updateWCheck(g.driver.driverid)
            elif action == 'Create':
                car.newWCheck(g.driver.driverid)
            else:
                flash("Invalid request ({})".format(action))
        else:
            flashformerrors(carform)

    except Exception as e:
        log.error("CarsPost: %s", e, exc_info=e)
        g.db.rollback()
        flash(str(e))
    return redirect(url_for('.cars'))


@Register.route("/<series>/events")
def events():
    events   = Event.byDate(ignoreexternal=True)
    cars     = {c.carid:c   for c in Car.getForDriver(g.driver.driverid)}
    registered = defaultdict(list)
    pitems     = defaultdict(list)
    accounts   = dict()
    showpay    = dict()
    for r in Registration.getForDriver(g.driver.driverid):
        r.classcode = cars[r.carid].classcode
        registered[r.eventid].append(r)
    for e in events:
        decorateEvent(e, len(registered[e.eventid]))
    for i in PaymentItem.getAll():
        pitems[i.accountid].append(i)
    for e in events:
        accounts[e.eventid] = PaymentAccount.get(e.accountid)
        showpay[e.eventid]  = accounts[e.eventid] and accounts[e.eventid].secret and any(len(r.payments) == 0 for r in registered[e.eventid])

    return render_template('register/events.html', events=events, cars=cars, registered=registered, accounts=accounts, showpay=showpay, pitems=pitems)


@Register.route("/<series>/help")
def help():
    return render_template('register/help.html')


def _renderSingleEvent(event, error):
    """ INTERNAL: For returning HTML for a single event div in response to updates """
    cars    = {c.carid:c for c in Car.getForDriver(g.driver.driverid)}
    reg     = [ r for r in Registration.getForDriver(g.driver.driverid) if r.eventid == event.eventid ]
    for r in reg: r.classcode = cars[r.carid].classcode

    account = PaymentAccount.get(event.accountid)
    showpay = account and account.secret and any(len(r.payments) == 0 for r in reg)
    decorateEvent(event, len(reg))

    eventdisplay = get_template_attribute('/register/macros.html', 'eventdisplay')
    return eventdisplay(event, cars, reg, showpay, error)


@Register.route("/<series>/sessionspost", methods=['POST'])
def sessionspost():
    pairs = list()
    for k,v in request.form.items():
        if v in ('y','on') or v is True:
            pairs.append((uuid.UUID(request.form['car-'+k]), k))
    return _eventspostinternal(request.form['eventid'], pairs)

@Register.route("/<series>/eventspost", methods=['POST'])
def eventspost():
    return _eventspostinternal(request.form['eventid'], [(uuid.UUID(k),'') for (k,v) in request.form.items() if v in ('y','on') or v is True])


def _eventspostinternal(eventid, pairs):
    """ Handles a add/change request from the user """
    error = ""
    event = None

    try:
        eventid  = uuid.UUID(eventid) #request.form['eventid'])
        event    = Event.get(eventid)
        curreg   = {(r.carid,r.session):r for r in Registration.getForDriver(g.driver.driverid) if r.eventid == event.eventid}
        oldids   = set([(r.carid,r.session) for r in curreg.values()])
        newids   = set(pairs)

        toadd    = set([Registration(carid=reg[0], eventid=eventid, session=reg[1], payments=[], modified=datetime.datetime.utcnow()) for reg in newids - oldids])
        nochange = set([curreg[x] for x in newids & oldids])
        todel    = set([curreg[x] for x in oldids - newids])

        paydests = list(nochange) + list(toadd)

        # If any of the deleted cars had a payment, we need to move that to an open unchanged or new registration
        for delr in list(filter(lambda r: len(r.payments), todel)):
            # Favor same session first, no payments second, then modified time
            if not len(paydests):
                raise FlashableException("Change aborted: would leave orphaned payment(s) as there were no registrations to move to")

            paydests.sort(key = lambda r: r.modified, reverse=True)
            paydests.sort(key = lambda r: len(r.payments))
            paydests.sort(key = lambda r: r.session==delr.session and 1 or 2)

            otherr = paydests[0]
            for p in delr.payments:
                otherr.payments.append(p)
                p.carid = otherr.carid
                p.session = otherr.session
                p.update()
            delr.payments = []

            if otherr in nochange:
                # Change logging requires primary key updates to delete and then insert, delete only uses primary key
                todel.add(otherr)
                toadd.add(otherr)


        # Check any limits with current registration
        mycount = len(curreg) + len(toadd) - len(todel)
        decorateEvent(event, mycount)
        if mycount > event.mylimit:
            raise FlashableException("Limit hit outside session, request aborted")

        for r in todel: r.delete()
        for r in toadd: r.insert()

    except FlashableException as fe:
        error = str(fe)
    except Exception as e:
        g.db.rollback()
        error = "Exception in processing has been logged"
        log.warning("exception in events post", exc_info=e)
        if not event:
            return str(e)

    return _renderSingleEvent(event, error)


@Register.route("/<series>/usednumbers")
def usednumbers():
    classcode = request.args.get('classcode', None)
    if classcode is None:
        return "missing data in request"
    return json_encode(sorted(list(Car.usedNumbers(g.driver.driverid, classcode, g.settings.superuniquenumbers))))


@Register.route("/<series>/rulesaccept", methods=['POST'])
def rulesaccept():
    if 'accept' in request.form:
        g.driver.setSeriesAttr('rulesack', True)
    return redirect(request.form.get('returnto', url_for('.events')))


@Register.route("/logout")
def logout():
    session.pop('driverid', None)
    return redirect(url_for('.index'))


####################################################################
# Unauthenticated functions

@Register.route("/<series>/view/<uuid:eventid>")
def view():
    event = Event.get(g.eventid)
    if event is None:
        raise InvalidEventException()
    g.classdata = ClassData.get()
    registered = defaultdict(list)
    for r in Registration.getForEvent(g.eventid, event.paymentRequired()):
        registered[r.session or r.classcode].append(r)
    return render_template('register/reglist.html', event=event, registered=registered)

@Register.route("/ical/<driverid>")
def ical(driverid):
    return ical_encode(getAllUpcoming(driverid))

@Register.route("/login", methods=['POST', 'GET'])
def login():
    if g.driver: return redirect_series()

    login = PasswordForm(prefix='login')
    reset = ResetForm(prefix='reset')
    register = RegisterForm(prefix='register')
    active = "login"
    hasemail = True #getattr(current_app, 'mail', None) is not None

    if login.submit.data:
        if login.validate_on_submit():
            try:
                user = Driver.byUsername(login.username.data)
                if user and current_app.hasher.check_password_hash(user.password, login.password.data):
                    session['driverid'] = user.driverid
                    return redirect_series(login.gotoseries.data)
                flash("Invalid username/password")
            except Exception as e:
                log.warning("password check error", exc_info=e)
                flash("Error: " + str(e))
        else:
            flashformerrors(login)

    elif reset.submit.data:
        active = "reset"
        if reset.validate_on_submit():
            for d in Driver.find(reset.firstname.data.strip(), reset.lastname.data.strip()):
                if d.email.lower() == reset.email.data.strip().lower():
                    token = current_app.usts.dumps({'request': 'reset', 'driverid': str(d.driverid)})
                    url = url_for('.reset', token=token, _external=True)
                    req = {'email':d.email, 'firstname':d.firstname, 'lastname':d.lastname}
                    EmailQueue.queueMessage(
                        subject = "Scorekeeper Reset Request",
                        recipient=req,
                        body = render_template("/register/resetemail.html", url=url)
                    )
                    return redirect(url_for(".emailsent", rcpt="{} {} <{}>".format(req['firstname'], req['lastname'], req['email'])))
            flash("No user could be found with those parameters")
        else:
            flashformerrors(reset)

    elif register.submit.data:
        active = "register"
        # FINISH ME, some kind of CAPTCHA here someday?  Maybe not.
        if register.validate_on_submit():
            if Driver.byNameEmail(register.firstname.data, register.lastname.data, register.email.data):
                flash("That combination of name/email already exists, please use the reset tab instead")
            elif Driver.byUsername(register.username.data) != None:
                flash("That username is already taken")
            else:
                req = {'request': 'register', 'firstname': register.firstname.data.strip(), 'lastname': register.lastname.data.strip(),
                                              'email':register.email.data.strip(), 'username': register.username.data.strip(), 'password': register.password.data}
                token = current_app.usts.dumps(req)
                if g.isonsite:
                    # Off main server (onsite), we let them register without the email verification, jump directly there
                    request.args = dict(token=token)
                    return finish()

                try:
                    host = req['email'].split('@')[1]
                    socket.gethostbyaddr(socket.gethostbyname(host))
                    if host in current_app.config['EMAIL_BLACKLIST']:
                        raise socket.error('blacklisted host')

                    url  = url_for('.finish', token=token, _external=True)
                    EmailQueue.queueMessage(
                        subject = "Scorekeeper Profile Request",
                        recipient=req,
                        body = render_template("/register/newprofileemail.html", url=url)
                    )
                except (socket.error, IndexError) as e:
                    log.warning("Ignore {} ({}; {})".format(req['email'], request.remote_addr, request.headers['X-Forwarded-For']))

                return redirect(url_for(".emailsent", rcpt="{} {} <{}>".format(req['firstname'], req['lastname'], req['email'])))
        else:
            flashformerrors(register)

    login.gotoseries.data = g.series
    login.username.data = request.args.get('username', '')
    register.gotoseries.data = g.series
    return render_template('/register/login.html', active=active, login=login, reset=reset, register=register, hasemail=hasemail)


@Register.route("/emailsent")
def emailsent():
    return render_template("/register/emailsent.html", rcpt=request.args.get('rcpt', ''), sender=os.environ['MAIL_SEND_FROM'], replyto=os.environ['MAIL_SEND_DEFAULT_REPLYTO'])


@Register.route("/finish")
def finish():
    try:
        req = current_app.usts.loads(request.args['token'], max_age=86400) # 1 day expiry
    except Exception as e:
        raise DisplayableError(header="Confirmation Error", content="Sorry, this confirmation token failed (%s)" % e.__class__.__name__) from e

    if req.get('request', '') != 'register':
        raise DisplayableError(header="Confirmation Error", content="Sorry, this confirmation token failed as the request type is incorrect")

    if Driver.byUsername(req['username']) != None:
        return render_template('/register/alreadycomplete.html', username=req['username'])

    session['driverid'] = Driver.new(req['firstname'], req['lastname'], req['email'], req['username'], req['password'])
    return redirect(url_for(".profile", askprofile=1))


@Register.route("/reset", methods=['GET', 'POST'])
def reset():
    form = PasswordForm()
    if form.submit.data and form.validate_on_submit():
        if 'driverid' not in session:
            abort(400, 'No driverid present during reset, how?')
        Driver.updatepassword(session['driverid'], form.username.data.strip(), form.password.data)
        return redirect_series("")

    elif request.method == 'GET':
        try:
            req = current_app.usts.loads(request.args['token'], max_age=86400) # 1 day expiry
        except Exception as e:
            raise DisplayableError(header="Confirmation Error", content="Sorry, this confirmation token failed (%s)" % e.__class__.__name__) from e

        if req.get('request', '') == 'reset':
            session['driverid'] = uuid.UUID(req['driverid'])
            return render_template("register/reset.html", form=form)

    elif form.errors:
        return render_template("register/reset.html", form=form, formerror=form.errors)

    raise DisplayableError(header="Confirmation Error", content="Unknown reset request type")


@Register.route("/<series>/unsubscribe")
def unsubscribe():
    error  = ""
    listid = ""
    driver = None
    try:
        req    = current_app.usts.loads(request.args['token'], max_age=8640000) # 100 day expiry
        driver = Driver.get(req['id'])
        listid = req['listid']
        if driver:
            Unsubscribe.set(driver.driverid, listid)
        else:
            error = "Unable to find a driver for id <b>{}</b>.  No list modifications have occured.".format(req['id'])
    except Exception as e:
        error = "Unable to unsubscribe: {}".format(e)

    return render_template("register/unsubscribe.html", driver=driver, error=error, listid=listid)


####################################################################
# Utility functions

def redirect_series(series=""):
    path = getRecordedPath(REGISTERKEY, None)
    if path:
        return redirect(path)
    if series and series in Series.active():
        return redirect(url_for(".events", series=series))
    return redirect(url_for(".index"))

def getAllUpcoming(driverid):
    upcoming = defaultdict(lambda: defaultdict(list))
    for s in Series.active():
        for r in Registration.getForSeries(s, driverid):
            if r.date >= datetime.datetime.utcnow().date():
                upcoming[r.date][s, r.name].append(r)
    return upcoming

def decorateEvent(e, mycount):
    e.drivercount  = e.getRegisteredDriverCount()
    e.entrycount   = e.getRegisteredCount()
    limits         = [[999, ""],]
    if e.sinlimit and e.drivercount >= e.sinlimit and mycount == 0:
        limits.append([0,          "The single entry limit of {} has been met".format(e.sinlimit)])
    if e.perlimit:
        limits.append([e.perlimit, "The personal entry limit of {} has been met".format(e.perlimit)])
    if e.totlimit:
        limits.append([e.totlimit - e.entrycount + mycount, "The total entry limit of {} has been met".format(e.totlimit)])

    (e.mylimit, e.limitmessage) = min(limits, key=lambda x: x[0])

