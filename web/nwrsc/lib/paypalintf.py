import datetime
import paypalrestsdk
import uuid

from flask import current_app, flash, g, redirect, request, url_for

from ..lib.misc import *
from ..model import Event, PaymentAccount, Payment, TempCache


def order(event, account, purchase, cache):
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

    localapi = paypalrestsdk.Api({'mode': 'live', 'client_id': account.accountid, 'client_secret': account.secret})
    payment  = paypalrestsdk.Payment(order, api=localapi)
    if payment.create():
        TempCache.put(payment.id, cache)
        return json_encode({'paymentID': payment.id})
    else:
        raise FlashableException(payment.error)


def executepayment():
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

        localapi = paypalrestsdk.Api({'mode': 'live', 'client_id': account.accountid, 'client_secret': account.secret})
        payment  = paypalrestsdk.Payment.find(paymentid, api=localapi)
        if not payment.execute({"payer_id": payerid}):
            raise FlashableException("Payment Error: " + payment.error)

        Payment.recordPayment(cached['eventid'], cached['refid'], cached['type'], paymentid, 
                    datetime.datetime.strptime(payment.create_time, '%Y-%m-%dT%H:%M:%SZ'),
                    cached['cars'])

        cached['verified'] = True
        TempCache.put(paymentid, cached)

    except FlashableException as fe:
        flash(str(fe))
    except Exception as e:
        flash("Exception in processing has been logged")
        log.warning(str(e), exc_info=e)

    return json_encode({'redirect': url_for(".events")})
