from collections import defaultdict
import datetime
import itertools
import logging
import uuid
import squareconnect
import time

import itsdangerous
from flask import abort, Blueprint, current_app, flash, g, get_template_attribute, redirect, request, render_template, Response, session, stream_with_context, url_for
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
            g.seriesname = Settings.get('seriesname')
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
    carform = CarForm(g.classdata)
    events  = {e.eventid:e for e in Event.byDate()}
    cars    = {c.carid:c   for c in Car.getForDriver(g.driver.driverid)}
    active  = defaultdict(set)
    for carid,eventid in Driver.activecars(g.driver.driverid):
        active[carid].add(eventid)
    classinglink = Settings.get("classinglink")
    return render_template('register/cars.html', events=events, cars=cars, active=active, carform=carform, classinglink=classinglink)


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

    events   = Event.byDate()
    cars     = {c.carid:c   for c in Car.getForDriver(g.driver.driverid)}
    registered = defaultdict(list)
    pitems     = defaultdict(list)
    accounts   = dict()
    showpay    = dict()
    for r in Registration.getForDriver(g.driver.driverid):
        registered[r.eventid].append(r)
    for e in events:
        decorateEvent(e, len(registered[e.eventid]))
    for i in PaymentItem.getAll():
        pitems[i.accountid].append(i)
    for e in events:
        accounts[e.eventid] = PaymentAccount.get(e.accountid)
        showpay[e.eventid] = e.accountid is not None and any(r.txid is None for r in registered[e.eventid])

    log.warning(showpay)
    return render_template('register/events.html', events=events, cars=cars, registered=registered, accounts=accounts, showpay=showpay, pitems=pitems)


def _renderSingleEvent(event, error):
    """ INTERNAL: For returning HTML for a single event div in response to updates """
    cars    = {c.carid:c for c in Car.getForDriver(g.driver.driverid)}
    reg     = [ r for r in Registration.getForDriver(g.driver.driverid) if r.eventid == event.eventid ]
    account = PaymentAccount.get(event.accountid)
    showpay = event.accountid is not None and any(r.txid is None for r in reg)
    decorateEvent(event, len(reg))

    eventdisplay = get_template_attribute('/register/macros.html', 'eventdisplay')
    return eventdisplay(event, cars, reg, showpay, error)


@Register.route("/<series>/eventspost", methods=['POST'])
def eventspost():
    """ Handles a add/change request from the user """
    if not g.driver: raise NotLoggedInException()
    error = ""

    try:
        eventid  = uuid.UUID(request.form['eventid'])
        event    = Event.get(eventid)
        curreg   = {r.carid:r for r in Registration.getForDriver(g.driver.driverid) if r.eventid == event.eventid}
        oldids   = set(curreg.keys())
        newids   = set([uuid.UUID(k) for (k,v) in request.form.items() if v == 'y' or v is True])

        toadd    = set([Registration(carid=x, eventid=eventid) for x in newids - oldids])
        nochange = set([curreg[x] for x in newids & oldids])
        todel    = set([curreg[x] for x in oldids - newids])

        # If any of the deleted cars had a payment, we need to move that to an open unchanged or new registration, favor old registrations
        for delr in todel:
            if not delr.txid: continue
            for otherr in list(nochange) + list(toadd):
                log.warning("check {}".format(otherr))
                if not getattr(otherr, 'txid', None):
                    otherr.txid     = delr.txid
                    otherr.txtime   = delr.txtime
                    otherr.itemname = delr.itemname
                    otherr.amount   = delr.amount
                    if otherr in nochange:
                        # Change logging requires primary key updates to delete and then insert, delete only uses primary key
                        todel.add(otherr) 
                        toadd.add(otherr)
                    break
            else:
                raise FlashableException("Change aborted, no available registered cars to move previous payment to")

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

    return json_encode({'html': _renderSingleEvent(event, error)})


@Register.route("/<series>/payment", methods=['POST'])
def payment():
    """ Handles a payment request from the user """
    if not g.driver: raise NotLoggedInException()

    error = ""
    try:
        eventid = uuid.UUID(request.form.get('eventid', None))
        event   = Event.get(eventid)
        account = PaymentAccount.get(event.accountid)
        items   = {i.itemid:i for i in PaymentItem.getForAccount(event.accountid)}
        if not len([1 for k,v in request.form.items() if k.startswith('pay-') and v]):
            raise Exception("No payment options selected")

        if account.type == 'square':
            refid    = "{}-order-{}".format(g.series, TempCache.nextorder())
            order    = squareconnect.models.CreateOrderRequest(reference_id=refid, line_items = [])
            checkout = squareconnect.models.CreateCheckoutRequest(
                        order = order,
                        idempotency_key = refid,
                        redirect_url    = url_for('.paymentcomplete', eventid=eventid, _external=True),
                        pre_populate_buyer_email = g.driver.email,
                        ask_for_shipping_address = True,
                        pre_populate_shipping_address = squareconnect.models.Address(
                            address_line_1 = g.driver.attr.get('address',''),
                            locality       = g.driver.attr.get('city', ''),
                            administrative_district_level_1 = g.driver.attr.get('state', ''),
                            postal_code    = g.driver.attr.get('zip', ''),
                            country        = g.driver.attr.get('country', 'US'),
                            first_name     = g.driver.firstname,
                            last_name      = g.driver.lastname
                        ))
            
            cache = { 
                'refid': refid,
                'eventid': str(eventid),
                'accountid': account.accountid,
                'type': account.type,
                'cars': {}
            }
            purchase = defaultdict(int)

            for key,itemid in request.form.items():
                if not key.startswith('pay-') or not itemid: continue
                carid = uuid.UUID(key[4:])
                cache['cars'][str(carid)] = {'name': items[itemid].name, 'amount':items[itemid].price/100 }
                purchase[itemid] += 1

            for itemid, count in purchase.items():
                if not count: continue
                order.line_items.append(
                    squareconnect.models.CreateOrderRequestLineItem(
                        catalog_object_id=itemid,
                        note="{} - {}".format(event.date.strftime("%m/%d/%Y"), event.name),
                        quantity=str(count)))

            client   = squareconnect.ApiClient(header_name='Authorization', header_value='Bearer '+account.secret)
            response = squareconnect.apis.checkout_api.CheckoutApi(api_client=client).create_checkout(account.accountid, checkout)
            cache['checkoutid'] = response.checkout.id
            TempCache.put(cache['refid'], cache)

            return json_encode({'redirect': response.checkout.checkout_page_url})

        else:
            error = "Unknown account type = {}".format(account.type)
            log.warning(error)

    except Exception as e:
        error = str(e)
        log.warning(error, exc_info=e)

    return json_encode({'html': _renderSingleEvent(event, error)})


@Register.route("/<series>/paymentcomplete")
def paymentcomplete():
    if not g.driver: raise NotLoggedInException()
    
    try:
        transactionid = request.args.get('transactionId', 'NoTransactionId')
        referenceid   = request.args.get('referenceId',   'NoReferenceId')
        cached        = TempCache.get(referenceid)

        if not cached:
            raise FlashableException("Missing order data to confirm payment with for reference '{}'".format(referenceid))
        if cached.get('verified', False):
            raise FlashableException("Order {} has already been verified".format(referenceid))

        eventid  = uuid.UUID(cached['eventid'])
        event    = Event.get(eventid)
        account  = PaymentAccount.get(event.accountid)
        client   = squareconnect.ApiClient(header_name='Authorization', header_value='Bearer '+account.secret)
        response = None

        # Square may call us back but there seems to be a delay before we can load the transaction to check, we retry at longer intervals
        for ii in range(5):
            time.sleep(ii+0.1)
            try:
                response = squareconnect.apis.transactions_api.TransactionsApi(api_client=client).retrieve_transaction(account.accountid, transactionid)
                break
            except:
                log.warning("transaction verification failed for {}".format(transactionid))

        if not response:
            raise FlashableException("Unable to verify transaction {} with Square, contact the administrator".format(transactionid))

        for reg in Registration.getForDriver(g.driver.driverid):
            caridstr = str(reg.carid)
            if reg.eventid != eventid or caridstr not in cached['cars']:
                continue
            if reg.txid and reg.txid != transactionid:
                flash("Warning: Overwrote transaction {} with {}".format(reg.txid, transactionid))
            reg.txid     = transactionid
            reg.txtime   = datetime.datetime.strptime(response.transaction.created_at, '%Y-%m-%dT%H:%M:%SZ')
            reg.itemname = cached['cars'][caridstr]['name']
            reg.amount   = cached['cars'][caridstr]['amount']
            reg.update()

        cached['verified'] = True
        TempCache.put(referenceid, cached)

    except FlashableException as fe:
        flash(str(fe))
    except Exception as e:
        flash("Exception in processing has been logged")
        log.warning(str(e), exc_info=e)
            
    return redirect(url_for(".events"))


@Register.route("/<series>/usednumbers")
def usednumbers():
    if not g.driver: raise NotLoggedInException()
    classcode = request.args.get('classcode', None)
    if classcode is None:
        return "missing data in request"
    superuniquenumbers = Settings.get("superuniquenumbers")
    return json_encode(sorted(list(Car.usedNumbers(g.driver.driverid, classcode, superuniquenumbers=superuniquenumbers))))


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
    seriesname = Settings.get("seriesname")
    g.classdata = ClassData.get()
    registered = defaultdict(list)
    for r in Registration.getForEvent(g.eventid, event.paymentRequired()):
        registered[r.classcode].append(r)
    return render_template('register/reglist.html', seriesname=seriesname, event=event, registered=registered)

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

