from collections import defaultdict
import datetime
import dateutil.parser
import http.client
import json
import logging
import time
import uuid

from flask import abort, current_app, flash, g, redirect, render_template, request, url_for

from .admin import isAuth, isSuperAuth
from .blueprints import *
from ..lib.encoding import json_encode, time_print
from ..lib.forms import formIntoAttrBase, PayPalAccountForm, PaymentItemForm
from ..lib.misc import *
import nwrsc.lib.paypalintf as paypalintf
import nwrsc.lib.squareintf as squareintf
from ..model import *

log = logging.getLogger(__name__)


######  The user registration pieces   ######

@Register.route("/<series>/order", methods=['POST'])
def order():
    """ Handles a order request from the user """
    if not g.driver: raise NotLoggedInException()

    error = ""
    event = None
    try:
        eventid = uuid.UUID(request.form.get('eventid', None))
        event   = Event.get(eventid)
        account = PaymentAccount.get(event.accountid)
        items   = {i.itemid:i for i in PaymentItem.getForAccount(event.accountid)}
        if not len([1 for k,v in request.form.items() if k.startswith('pay+') and v]):
            return json_encode({'error': 'No payment options selected'})

        cache = {
            'refid':     "{}-order-{}".format(g.series, TempCache.nextorder()),
            'eventid':   str(event.eventid),
            'accountid': account.accountid,
            'type':      account.type,
            'cars':      []
        }

        purchase = defaultdict(int)
        for key,itemid in request.form.items():
            if not key.startswith('pay+') or not itemid: continue
            args = key.split('+')
            if len(args) != 3: continue

            cache['cars'].append({'carid': args[1], 'session': args[2], 'name': items[itemid].name, 'amount':items[itemid].price/100 })
            purchase[items[itemid]] += 1

        return {'square': squareintf.order,
                'paypal': paypalintf.order,
        }.get(account.type, unknownorder)(event, account, purchase, cache)

    except Exception as e:
        error = str(e)
        log.warning(error, exc_info=e)

    return json_encode({'error': error})

def unknownorder(event, account, purchase, cache):
    raise Exception("Unknown account type '{}'".format(account.type))

@Register.route("/<series>/paypalexecute", methods=['POST'])
def paypalexecute():
    if not g.driver: raise NotLoggedInException()
    return paypalintf.executepayment()

@Register.route("/<series>/sqaureexecute", methods=['POST'])
def sqaurefinishpayment():
    if not g.driver: raise NotLoggedInException()
    return squareintf.executepayment()

######  The administration pieces   ######

@Admin.route("/payments")
def payments():
    return render_template('/admin/payments.html', events=g.events)

@Admin.route("/paymentlist")
def paymentlist():
    payments = Payment.getAll()
    unsub = Unsubscribe.getUnsub(Settings.get('emaillistid'))
    for p in payments:
        p.txtime = time_print(p.txtime, '%Y-%m-%d %H:%M %Z') 
        if p.optoutmail or p.driverid in unsub:
            p.email = '********'
    return json_encode(payments)

@Admin.route("/delaccount", methods=['POST'])
def delaccount():
    log.debug("Delete " + request.form['accountid'])
    try:
        PaymentAccount.deleteById(request.form['accountid'])
    except Exception as e:
        log.warning("Delete account error", exc_info=e)
        return json_encode({'error': str(e)})
    return json_encode({"success": True})

@Admin.route("/delitem", methods=['POST'])
def delitem():
    try:
        PaymentItem.deleteById(request.form['itemid'])
    except Exception as e:
        log.warning("Delete item error", exc_info=e)
        return json_encode({'error': str(e)})
    return json_encode({"success": True})


@Admin.route("/accounts", methods=['GET', 'POST'])
def accounts():
    action = request.form.get('submit')
    ppacctform = PayPalAccountForm()
    itemform   = PaymentItemForm()

    if action == 'Select Location': # Finishing Square OAuth
        try:
            tdata = current_app.usts.loads(request.form['tdata'], max_age=36000) # 10 hour expiry
            ldata = current_app.usts.loads(request.form['ldata'], max_age=36000)
            location = ldata[request.form['locationid']]

            p = PaymentAccount()
            p.accountid = location['id']
            p.name      = location['name']
            p.type      = "square"
            p.attr      = { 'expires': tdata['expires_at'], 'merchantid': tdata['merchant_id'] } 
            p.upsert()

            PaymentItem.deleteByAccountId(p.accountid) # Delete previous if existing
            for _,item in location['items'].items():
                i = PaymentItem()
                i.itemid    = item['itemid']
                i.accountid = location['id']
                i.name      = item['name']
                i.price     = item['price']
                i.currency  = item['currency']
                i.upsert()
 
            s = PaymentSecret()
            s.accountid = p.accountid
            s.secret    = tdata['access_token']
            s.upsert()
        except Exception as e:
            g.db.rollback()
            log.warning(e, exc_info=e)
            flash("Inserting new payment account failed: " + str(e))
        return redirect(url_for('.accounts'))

    elif action == 'Add PayPal Account':

        if ppacctform.validate():
            p = PaymentAccount()
            p.accountid = ppacctform.accountid.data
            p.name      = ppacctform.name.data
            p.type      = "paypal"
            p.attr      = { }
            p.insert()

            s = PaymentSecret()
            s.accountid = ppacctform.accountid.data
            s.secret    = ppacctform.secret.data
            s.insert()
        else:
            flashformerrors(ppacctform)
        return redirect(url_for('.accounts'))

    elif action == 'Add Item':

        if itemform.validate():
            item = PaymentItem()
            item.itemid    = str(uuid.uuid1())
            item.accountid = itemform.accountid.data
            item.name      = itemform.name.data
            item.price     = itemform.price.data * 100
            item.currency  = "USD"
            item.insert()
        else:
            flashformerrors(itemform)
        return redirect(url_for('.accounts'))

    accounts  = PaymentAccount.getAll()
    items     = PaymentItem.getAll()
    
    return render_template('/admin/paymentaccounts.html', accounts=accounts, items=items, squareurl=squareintf.oauth_url, ppacctform=ppacctform, itemform=itemform)

def paymentscron():
    squareintf.periodic()

@Admin.endpoint("Admin.squareoauth")
def squareoauth():
    g.series = request.args.get('state', '')
    log.warning("auth {} {} {}".format(g.series, isAuth(g.series), session))
    if not isSuperAuth() and not isAuth(g.series):
        raise NotLoggedInException()
    squareintf.oauth()