from collections import defaultdict
import datetime
import itertools
import logging
import uuid
import time

import itsdangerous
from flask import abort, Blueprint, current_app, flash, g, get_template_attribute, redirect, request, render_template, session, url_for
from flask_mail import Message

from nwrsc.model import *
from nwrsc.lib.forms import *
from nwrsc.lib.misc import *
from nwrsc.lib.encoding import json_encode, ical_encode

log = logging.getLogger(__name__)

Register = Blueprint("Register", __name__) 

@Register.before_request
def setup():
    g.title = 'Scorekeeper Registration'
    g.activeseries = Series.active()
    g.selection = request.endpoint
    if 'driverid' in session:
        g.driver = Driver.get(session['driverid'])
        if g.series:
            if g.seriestype != Series.ACTIVE:
                raise ArchivedSeriesException()
            g.classdata = ClassData.get()
    else:
        g.driver = None

####################################################################
# Authenticated functions

@Register.route("/")
def index():
    if not g.driver: return login()
    g.selection = 'Register.events'
    return render_template('register/bluebase.html')

@Register.route("/<series>/")
def series():
    """ If logged in, just redirect to events """
    if not g.driver: return login()
    return redirect(url_for('.events'))


@Register.route("/profile")
@Register.route("/<series>/profile")
def profile():
    if not g.driver: return login()
    form        = DriverForm()
    upcoming    = getAllUpcoming(g.driver.driverid)
    attrBaseIntoForm(g.driver, form)
    return render_template('register/profile.html', form=form, upcoming=upcoming, surpressmenu=True)

@Register.route("/profilepost", methods=['POST'])
@Register.route("/<series>/profilepost", methods=['POST'])
def profilepost():
    form = DriverForm()
    if form.validate_on_submit():
        formIntoAttrBase(form, g.driver)
        g.driver.update()
    flashformerrors(form)
    return redirect(url_for('.profile'))


@Register.route("/<series>/cars")
def cars():
    if not g.driver: return login()
    settings = Settings.get()
    carform = CarForm(g.classdata)
    events  = {e.eventid:e for e in Event.byDate()}
    cars    = {c.carid:c   for c in Car.getForDriver(g.driver.driverid)}
    active  = defaultdict(set)
    for carid,eventid in Driver.activecars(g.driver.driverid):
        active[carid].add(eventid)
    return render_template('register/cars.html', events=events, cars=cars, active=active, carform=carform, settings=settings)


@Register.route("/<series>/carspost", methods=['POST'])
def carspost():
    if not g.driver: return login()
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
    if not g.driver: return login()

    sqappid  = current_app.config.get('SQ_APPLICATION_ID', '')
    events   = Event.byDate()
    cars     = {c.carid:c   for c in Car.getForDriver(g.driver.driverid)}
    registered = defaultdict(list)
    payments   = defaultdict(float)
    for r in Registration.getForDriver(g.driver.driverid):
        registered[r.eventid].append(r)
    for e in events:
        decorateEvent(e, len(registered[e.eventid]))
    for p in Payment.getForDriver(g.driver.driverid):
        payments[p.eventid] += p.amount

    return render_template('register/events.html', events=events, cars=cars, registered=registered, payments=payments, sqappid=sqappid)


@Register.route("/<series>/eventspost", methods=['POST'])
def eventspost():
    if not g.driver: raise NotLoggedInException()

    try:
        error   = ""
        eventid = uuid.UUID(request.form['eventid'])
        carids  = [uuid.UUID(k) for (k,v) in request.form.items() if v == 'y' or v is True]
        curreg  = len([r.carid for r in Registration.getForDriver(g.driver.driverid) if r.eventid == eventid])
        event   = Event.get(eventid)
        payments= Payment.getForDriverEvent(g.driver.driverid, eventid)
        minpay  = max(event.getMinCost(), 0.01)
        decorateEvent(event, curreg) # Figure out limit with current registration
        if len(carids) > event.mylimit:
            error = "Limit hit outside session, request aborted"
        else:
            pairs = [[cid, None] for cid in carids]
            total = 0
            idx = 0
            for p in payments:  # reassign payments to registrations
                total += p.amount
                while total >= minpay and idx < len(pairs):
                    pairs[idx][1] = p.txid
                    idx += 1
                    total -= minpay
                    log.info("{}, {}".format(total, minpay))

            Registration.update(eventid, pairs, g.driver.driverid)
    except Exception as e:
        g.db.rollback()
        log.warning("exception in events post: " + str(e), exc_info=e)
        return "<div class='error'>{}</div>".format(e)

    cars    = {c.carid:c for c in Car.getForDriver(g.driver.driverid)}
    reg     = [ r for r in Registration.getForDriver(g.driver.driverid) if r.eventid == eventid ]
    sqappid = current_app.config.get('SQ_APPLICATION_ID', '')
    decorateEvent(event, len(reg))
    if payments:
        paid = sum(p.amount for p in payments)
    else:
        paid = 0.0

    eventdisplay = get_template_attribute('/register/macros.html', 'eventdisplay')
    return eventdisplay(event, cars, reg, paid, sqappid, error)


@Register.route("/<series>/squarepayment", methods=['POST'])
def squarepayment():
    return "square payment {}".format(request.form)


@Register.route("/<series>/usednumbers")
def usednumbers():
    if not g.driver: raise NotLoggedInException()
    classcode = request.args.get('classcode', None)
    if classcode is None:
        return "missing data in request"

    g.settings = Settings.get()
    return json_encode(sorted(list(Car.usedNumbers(g.driver.driverid, classcode, g.settings.superuniquenumbers))))


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
    g.settings = Settings.get()
    g.classdata = ClassData.get()
    registered = defaultdict(list)
    for r in Registration.getForEvent(g.eventid, event.paymentRequired()):
        registered[r.classcode].append(r)
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
    hasemail = getattr(Register, 'mail', None) is not None

    if login.submit.data:
        if login.validate_on_submit():
            user = Driver.byUsername(login.username.data)
            if user and user.password == login.password.data:
                session['driverid'] = user.driverid
                return redirect_series(login.gotoseries.data)
            flash("Invalid username/password")
        else:
            flashformerrors(login)

    elif reset.submit.data:
        active = "reset"
        if reset.validate_on_submit():
            for d in Driver.find(reset.firstname.data, reset.lastname.data):
                if d.email.lower() == reset.email.data.lower():
                    token = current_app.usts.dumps({'request': 'reset', 'driverid': str(d.driverid)})
                    msg = Message("Scorekeeper Reset Request", recipients=[d.email])
                    msg.body = "Use the following link to continue the reset process.\n\n{}".format(url_for('.reset', token=token, _external=True))
                    Register.mail.send(msg)
                    return redirect(url_for(".emailsent"))
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
                email = register.email.data.strip()
                token = current_app.usts.dumps({'request': 'register', 'firstname': register.firstname.data.strip(), 'lastname': register.lastname.data.strip(),
                                            'email':email, 'username': register.username.data.strip(), 'password': register.password.data.strip()})
                msg = Message("Scorekeeper Profile Request", recipients=[email])
                msg.body = "Use the following link to complete the registration process.\n\n{}".format(url_for('.finish', token=token, _external=True))
                Register.mail.send(msg)
                return redirect(url_for(".emailsent"))
        else:
            flashformerrors(register)

    login.gotoseries.data = g.series
    register.gotoseries.data = g.series
    return render_template('/register/login.html', active=active, login=login, reset=reset, register=register, hasemail=hasemail)
        

@Register.route("/emailsent")
def emailsent():
    return render_template("common/simple.html", content="An email as been sent with a link to finish your registration/reset.")


@Register.route("/finish")
def finish():
    try:
        req = current_app.usts.loads(request.args['token'], max_age=3600) # 1 hour expiry
    except Exception as e:
        raise DisplayableError(header="Confirmation Error", content="Sorry, this confirmation token failed (%s)" % e.__class__.__name__) from e

    if req.get('request', '') != 'register':
        raise DisplayableError(header="Confirmation Error", content="Sorry, this confirmation token failed as the request type is incorrect")
    session['driverid'] = Driver.new(req['firstname'], req['lastname'], req['email'], req['username'], req['password'])
    return redirect(url_for(".profile"))


@Register.route("/reset", methods=['GET', 'POST'])
def reset():
    form = PasswordForm()
    if form.submit.data and form.validate_on_submit():
        if 'driverid' not in session: 
            abort(400, 'No driverid present during reset, how?')
        Driver.updatepassword(session['driverid'], form.username.data, form.password.data)
        return redirect_series("")

    elif request.method == 'GET':
        try:
            req = current_app.usts.loads(request.args['token'], max_age=3600) # 1 hour expiry
        except Exception as e:
            raise DisplayableError(header="Confirmation Error", content="Sorry, this confirmation token failed (%s)" % e.__class__.__name__) from e
    
        if req.get('request', '') == 'reset':
            session['driverid'] = uuid.UUID(req['driverid'])
            return render_template("register/reset.html", form=form)

    elif form.errors:
        return render_template("register/reset.html", form=form, formerror=form.errors)

    raise DisplayableError(header="Confirmation Error", content="Unknown reset request type")

 
####################################################################
# Utility functions

def redirect_series(series=""):
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

