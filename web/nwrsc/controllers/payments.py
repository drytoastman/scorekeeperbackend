from collections import defaultdict
import datetime
import dateutil.parser
import http.client
import json
import logging
import paypalrestsdk
import squareconnect
import time
import uuid
import pytz

from flask import current_app, flash, g, redirect, render_template, request, url_for

from .admin import isAuth, isSuperAuth
from .blueprints import *
from ..lib.encoding import json_encode
from ..lib.forms import formIntoAttrBase, PayPalAccountForm, PaymentItemForm
from ..lib.misc import *
from ..model import *

log = logging.getLogger(__name__)


######  The user registration pieces   ######


@Register.route("/<series>/payment", methods=['POST'])
def payment():
    """ Handles a payment request from the user """
    if not g.driver: raise NotLoggedInException()

    error = ""
    event = None
    try:
        eventid = uuid.UUID(request.form.get('eventid', None))
        event   = Event.get(eventid)
        account = PaymentAccount.get(event.accountid)
        items   = {i.itemid:i for i in PaymentItem.getForAccount(event.accountid)}
        if not len([1 for k,v in request.form.items() if k.startswith('pay-') and v]):
            return json_encode({'error': 'No payment options selected'})

        cache = { 
            'refid':     "{}-order-{}".format(g.series, TempCache.nextorder()),
            'eventid':   str(event.eventid),
            'accountid': account.accountid,
            'type':      account.type,
            'cars':      {}
        }

        purchase = defaultdict(int)
        for key,itemid in request.form.items():
            if not key.startswith('pay-') or not itemid: continue
            carid = uuid.UUID(key[4:])
            cache['cars'][str(carid)] = {'name': items[itemid].name, 'amount':items[itemid].price/100 }
            purchase[items[itemid]] += 1

        return {'square': _squarepayment,
                'paypal': _paypalpayment,
        }.get(account.type,   _unknownpayment)(event, account, purchase, cache)

        return response

    except Exception as e:
        error = str(e)
        log.warning(error, exc_info=e)

    return json_encode({'error': error})


def _unknownpayment(event, account, purchase, cache):
    raise Exception("Unknown account type '{}'".format(account.type))

def _paypalpayment(event, account, purchase, cache):

    items = []
    total = 0
    for item, count in purchase.items():
        if not count: continue
        items.append({
            "name":        item.name,
            "description": "{} - {}".format(event.date.strftime("%m/%d/%Y"), event.name),
            "quantity":    str(count),
            "price":       "{0:.2f}".format(item.price/100.0),
            "currency":    "USD"
        })
        total += count * item.price

    order = {
        "intent": "sale",
        "payer": { "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": url_for('.paypalexecute'),
            "cancel_url": url_for('.events') },
        "transactions": [{
            "reference_id": cache['refid'],
            "item_list": { "items": items },
            "amount":  {
                "currency": "USD",
                "total":    "{0:.2f}".format(total/100.0)
            }
            #"description": "Scorekeeper Online Payment"
        }]
    }

    localapi = paypalrestsdk.Api({'mode': 'sandbox', 'client_id': account.accountid, 'client_secret': account.secret})
    payment  = paypalrestsdk.Payment(order, api=localapi)
    if payment.create():
        TempCache.put(payment.id, cache)
        return json_encode({'paymentID': payment.id})
    else:
        raise FlashableException(payment.error)


def _squarepayment(event, account, purchase, cache):
    order    = squareconnect.models.CreateOrderRequest(reference_id=cache['refid'], line_items = [])
    checkout = squareconnect.models.CreateCheckoutRequest(
                order = order,
                idempotency_key = cache['refid'],
                redirect_url    = url_for('.sqaurepaymentcomplete', eventid=event.eventid, _external=True),
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
    
    for item, count in purchase.items():
        if not count: continue
        order.line_items.append(
            squareconnect.models.CreateOrderRequestLineItem(
                catalog_object_id=item.itemid,
                note="{} - {}".format(event.date.strftime("%m/%d/%Y"), event.name),
                quantity=str(count)))

    client   = squareconnect.ApiClient(header_name='Authorization', header_value='Bearer '+account.secret)
    response = squareconnect.apis.checkout_api.CheckoutApi(api_client=client).create_checkout(account.accountid, checkout)
    cache['checkoutid'] = response.checkout.id
    TempCache.put(cache['refid'], cache)

    return json_encode({'redirect': response.checkout.checkout_page_url})


def _recordPayment(cached, newtxid, newtxtime):
    p         = Payment()
    p.payid   = uuid.uuid1()
    p.eventid = uuid.UUID(cached['eventid'])
    p.refid   = cached['refid']
    p.txtype  = cached['type']
    p.txid    = newtxid
    p.txtime  = newtxtime

    for caridstr, entry in cached['cars'].items():
        p.carid    = uuid.UUID(caridstr)
        p.itemname = entry['name']
        p.amount   = entry['amount']
        p.insert()


@Register.route("/<series>/paypalexecute", methods=['POST'])
def paypalexecute():
    if not g.driver: raise NotLoggedInException()
    
    try:
        paymentid = request.form.get('paymentID', 'NoPaymentId')
        payerid   = request.form.get('payerID',   'NoPayerId')
        cached    = TempCache.get(paymentid)

        if not cached:
            raise FlashableException("Missing order data to confirm payment with for paymentid '{}'".format(paymentid))
        if cached.get('verified', False):
            raise FlashableException("Payment {} has already been executed".format(paymentid))

        eventid   = uuid.UUID(cached['eventid'])
        event     = Event.get(eventid)
        account   = PaymentAccount.get(event.accountid)

        localapi = paypalrestsdk.Api({'mode': 'sandbox', 'client_id': account.accountid, 'client_secret': account.secret})
        payment  = paypalrestsdk.Payment.find(paymentid, api=localapi)
        if not payment.execute({"payer_id": payerid}):
            raise FlashableError("Payment Error: " + payment.error)

        _recordPayment(cached, paymentid, datetime.datetime.strptime(payment.create_time, '%Y-%m-%dT%H:%M:%SZ'))
        cached['verified'] = True
        TempCache.put(paymentid, cached)

    except FlashableException as fe:
        flash(str(fe))
    except Exception as e:
        flash("Exception in processing has been logged")
        log.warning(str(e), exc_info=e)

    return json_encode({'redirect': url_for(".events")})



@Register.route("/<series>/sqaurepaymentcomplete")
def sqaurepaymentcomplete():
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

        _recordPayment(cached, transactionid, datetime.datetime.strptime(response.transaction.created_at, '%Y-%m-%dT%H:%M:%SZ'))
        cached['verified'] = True
        TempCache.put(referenceid, cached)

    except FlashableException as fe:
        flash(str(fe))
    except Exception as e:
        flash("Exception in processing has been logged")
        log.warning(str(e), exc_info=e)
            
    return redirect(url_for(".events"))


######  The administration pieces   ######


@Admin.route("/payments")
def payments():
    return render_template('/admin/payments.html', events=g.events)

@Admin.route("/paymentlist")
def paymentlist():
    payments = Payment.getAll()
    for p in payments:
        p.txtime = p.txtime.astimezone(datetime.timezone.utc).astimezone(pytz.timezone('US/Pacific'))
    return json_encode(payments)

@Admin.route("/delaccount", methods=['POST'])
def delaccount():
    log.debug("Delete " + request.form['accountid'])
    try:
        PaymentAccount.delete(request.form['accountid'])
    except Exception as e:
        log.warning("Delete account error", exc_info=e)
        return json_encode({'error': str(e)})
    return json_encode({"success": True})

@Admin.route("/delitem", methods=['POST'])
def delitem():
    try:
        PaymentItem.delete(request.form['itemid'])
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

    squareurl =  ''
    accounts  = PaymentAccount.getAll()
    items     = PaymentItem.getAll()
    sqappid   = current_app.config.get('SQ_APPLICATION_ID', '')
    if sqappid:
        squareurl = 'https://connect.squareup.com/oauth2/authorize?client_id={}&scope=MERCHANT_PROFILE_READ,PAYMENTS_WRITE,ORDERS_WRITE,ITEMS_READ&state={}'.format(sqappid, g.series)

    return render_template('/admin/paymentaccounts.html', accounts=accounts, items=items, squareurl=squareurl, ppacctform=ppacctform, itemform=itemform, ismainserver=current_app.config['IS_MAIN_SERVER'])


@Admin.endpoint("Admin.squareoauth")
def squareoauth():
    """ Special endpoint out of the normal URL pattern space as it has to be statically set in the Square control panel """
    g.series = request.args.get('state', '')
    if not isSuperAuth() and not isAuth(g.series):
        raise NotLoggedInException()
    with g.db.cursor() as cur:
        cur.execute("SET search_path=%s,'public'; commit; begin", (g.series,))

    try:
        authorization_code = request.args.get('code', None)
        if not authorization_code:
            flash('Authorization Failed')
            return redirect(url_for('.accounts'))

        tokenresponse = square_oauth_gettoken(authorization_code)
        tokenresponse['expires_at'] = str(dateutil.parser.parse(tokenresponse['expires_at']))

        # Obtain the list of locations and items
        client = squareconnect.ApiClient(header_name='Authorization', header_value='Bearer '+tokenresponse['access_token'])
        locresponse = squareconnect.apis.locations_api.LocationsApi(api_client=client).list_locations()
        if locresponse.errors:
            raise Exception(locresponse.errors)

        catresponse = squareconnect.apis.catalog_api.CatalogApi(api_client=client).list_catalog()
        if catresponse.errors:
            raise Exception(catesponse.errors)

        # Prepare a reduced list of locations and their associated items
        locations = dict()
        for l in locresponse.locations:
            if l.status.lower() not in ('active',):
                continue

            loc = {
                   'id': l.id,
                 'name': l.name,
                'items': dict()
            }
            locations[l.id] = loc

            for obj in catresponse.objects:
                if obj.is_deleted or not obj.type == 'ITEM':
                    continue
                if obj.present_at_all_locations or loc['id'] in obj.present_at_location_ids:
                    idata = obj.item_data
                    var0  = idata.variations[0]
                    vdata = var0.item_variation_data
                    loc['items'][var0.id] = {
                            'name': idata.name,
                     'description': idata.description,
                          'itemid': var0.id,
                           'price': vdata.price_money.amount,
                        'currency': vdata.price_money.currency
                    }

        tdata = current_app.usts.dumps(tokenresponse)
        ldata = current_app.usts.dumps(locations)
        return render_template('/admin/locationselect.html', locations=locations, tdata=tdata, ldata=ldata)

    except Exception as e:
        log.warning(e)
        if len(e.args):
           flash(e.args[0])
        elif hasattr(e, 'body'):
            flash(e.body)
        else:
            flash(str(e))
        return redirect(url_for('.accounts'))


def square_oauth_gettoken(authorization_code):
    """ Perform the second half of the oauth process, why is this not in their SDK? """
    appid     = current_app.config.get('SQ_APPLICATION_ID', '')
    appsecret = current_app.config.get('SQ_APPLICATION_SECRET', '')
    if not appid or not appsecret:
        raise Exception('There is no square applcation setup in the local configuration')

    oauth_headers = {
      'Authorization': 'Client '+appsecret,
      'Accept':        'application/json',
      'Content-Type':  'application/json'
    }

    oauth_request = {
      'client_id': appid,
      'client_secret': appsecret,
      'code': authorization_code,
    }

    connection = http.client.HTTPSConnection('connect.squareup.com')
    connection.request('POST', '/oauth2/token', json.dumps(oauth_request), oauth_headers)
    response = json.loads(connection.getresponse().read())
    if not response.get('access_token', ''):
        raise Exception('Code exchange failed: ' + str(response))

    return response
