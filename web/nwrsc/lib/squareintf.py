import datetime
import logging
import pdb
import square
import square.client
import time
import uuid

from flask import current_app, flash, g, redirect, request, url_for

from ..lib.misc import *
from ..lib.encoding import json_encode
from ..model import Event, PaymentAccount, Payment, TempCache

log = logging.getLogger(__name__)


def order(event, account, purchase, cache):
    body = {
            'idempotency_key': cache['refid'],
            'order': {
                'location_id': account.accountid,
                'reference_id': cache['refid'],
                'line_items': [],
            }
        }

    for entry in cache['cars']:
        body['order']['line_items'].append({
            'name': "{} - {}".format(event.date.strftime("%m/%d/%Y"), event.name),
            'variation_name': entry['name'],
            'quantity': "1",
            "base_price_money": {
                "amount": entry['amount']*100,
                "currency": "USD"
            }
        })

    client = square.client.Client(access_token=account.secret, environment=account.attr['environment'] or 'production')
    response = client.orders.create_order(account.accountid, body)
    
    if response.is_error():
        raise Exception(response.errors)

    cache['orderid'] = response.body['order']['id']
    cache['total']   = response.body['order']['total_money']['amount']
    TempCache.put(cache['refid'], cache)

    return json_encode({'refid': cache['refid']})


def executepayment():
    payment = {
        "source_id": "cnon:card-nonce-ok",
        "idempotency_key": "ikey",
        "amount_money": response.body['order']['total_money'],
        "order_id": cache['orderid'],
        "billing_address": {
            'address_line_1' : g.driver.attr.get('address',''),
            'locality'       : g.driver.attr.get('city', ''),
            'administrative_district_level_1' : g.driver.attr.get('state', ''),
            'postal_code'    : g.driver.attr.get('zip', ''),
            'country'        : g.driver.attr.get('country', 'US'),
            'first_name'     : g.driver.firstname,
            'last_name'      : g.driver.lastname
        }
    }

    response = client.payments.create_payment(payment)
    if response.is_error():
        raise Exception(response.errors)

    Payment.recordPayment(cached['eventid'], cached['refid'], cached['type'], transactionid, 
                    datetime.datetime.strptime(response.transaction.created_at, '%Y-%m-%dT%H:%M:%SZ'),
                    cached['cars'])


"""
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
        api      = squareconnect.apis.transactions_api.TransactionsApi()
        response = None

        api.api_client.configuration.access_token = account.secret

        # Square may call us back but there seems to be a delay before we can load the transaction to check, we retry at longer intervals
        savee = None
        for ii in range(5):
            time.sleep(ii+0.1)
            try:
                response = api.retrieve_transaction(account.accountid, transactionid)
                break
            except Exception as e:
                savee = e
                log.warning("transaction verification failed for {}".format(transactionid))

        if not response:
            if savee: log.error("exception on last try was: {}".format(savee), exc_info=savee)
            raise FlashableException("Unable to verify transaction {} with Square, contact the administrator".format(transactionid))

        Payment.recordPayment(eventid, referenceid, 'square', transactionid, 
                    datetime.datetime.strptime(response.transaction.created_at, '%Y-%m-%dT%H:%M:%SZ'),
                    cached['cars'])
        cached['verified'] = True
        TempCache.put(referenceid, cached)

    except FlashableException as fe:
        flash(str(fe))
    except Exception as e:
        flash("Exception in processing has been logged")
        log.warning(str(e), exc_info=e)
            
    return redirect(url_for(".events"))
"""


def periodic():
    appid     = current_app.config.get('SQ_APPLICATION_ID', '')
    appsecret = current_app.config.get('SQ_APPLICATION_SECRET', '')
    if not appid or not appsecret:
        raise Exception('paymentscron will not work, there is no square applcation setup in the local configuration')

    with g.db.cursor() as cur:
        for s in Series.active():
            cur.execute("SET search_path=%s,'public'; commit; begin", (s,))
            for p in PaymentAccount.getAll():
                if 'expires' not in p.attr:
                    continue
                if p.type != 'square':  # Only do square renewals right now
                    continue
                expiresin = (dateutil.parser.parse(p.attr['expires']).replace(tzinfo=None) - datetime.datetime.now()).total_seconds()
                if expiresin > 259200: # More than 5 days to expiry, ignore it
                    continue

                try:
                    # Do the oauth call to get a new token
                    log.info("{} {} expires in {} seconds, renewing".format(s, p.accountid, expiresin))
                    oauth = squareconnect.OAuthApi()
                    oauth.api_client.configuration.api_key['Authorization'] = appsecret
                    oauth.api_client.configuration.api_key_prefix['Authorization'] = 'Client'
                    response = oauth.renew_token(appid, squareconnect.RenewTokenRequest(access_token=p.secret))

                    p.attr['expires'] = str(dateutil.parser.parse(response.expires_at))
                    p.update()

                    s = PaymentSecret()
                    s.accountid = p.accountid
                    s.secret    = response.access_token
                    s.upsert()

                except Exception as e:
                    log.warning("{} - {} renewal failure: {}".format(s, p.accountid, e))
                    if expiresin < 0:
                        log.warning("Removing payment account as renewal failed too many times")
                        PaymentAccount.deleteById(p.accountid)

    return ""


def oauth_url():
    sqappid   = current_app.config.get('SQ_APPLICATION_ID', '')
    if sqappid:
        return 'https://connect.squareup.com/oauth2/authorize?client_id={}&scope=MERCHANT_PROFILE_READ,PAYMENTS_WRITE,PAYMENTS_READ,ORDERS_WRITE,ITEMS_READ&state={}'.format(sqappid, g.series)


def oauth():
    """ Special endpoint out of the normal URL pattern space as it has to be statically set in the Square control panel """
    with g.db.cursor() as cur:
        cur.execute("SET search_path=%s,'public'; commit; begin", (g.series,))

    try:
        appid     = current_app.config.get('SQ_APPLICATION_ID', '')
        appsecret = current_app.config.get('SQ_APPLICATION_SECRET', '')
        if not appid or not appsecret:
            raise Exception('There is no square applcation setup in the local configuration')

        authorization_code = request.args.get('code', None)
        if not authorization_code:
            raise Exception('No authorization code was provided to oauth endpoint')

        # Do the oauth call to get a new token
        oauth = squareconnect.OAuthApi()
        oauth.api_client.configuration.access_token = appsecret
        tokenresponse = oauth.obtain_token(squareconnect.ObtainTokenRequest(client_id=appid, client_secret=appsecret, code=authorization_code))

        # Setup client with new access token and get the list of locations and items
        conf = squareconnect.Configuration()
        conf.access_token = tokenresponse.access_token
        client = squareconnect.ApiClient(conf)

        locresponse = squareconnect.apis.locations_api.LocationsApi(client).list_locations()
        if locresponse.errors:
            raise Exception(locresponse.errors)
        if not locresponse.locations:
            raise Exception("No Locations found in Square account, there must be at least one")

        catresponse = squareconnect.apis.catalog_api.CatalogApi(client).list_catalog()
        if catresponse.errors:
            raise Exception(catesponse.errors)
        if not catresponse.objects:
            raise Exception("No Items found in Square account, there must be at least one")

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

        tdata = current_app.usts.dumps({
                    'access_token': tokenresponse.access_token,
                    'expires_at':   str(dateutil.parser.parse(tokenresponse.expires_at)),
                    'merchant_id':  tokenresponse.merchant_id
                })

        locations = {k:v for k,v in locations.items() if v['items']}
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