import dateutil.parser
import http.client
import logging
import json
import uuid

from flask import current_app, flash, g, redirect, request, url_for

from nwrsc.model import Payment, PaymentAccount, PaymentAccountSecret

log = logging.getLogger(__name__)

def square_payment(event, account, driver, amount, nonce):
    headers = {
        'Authorization': 'Bearer ' + account.secret,
        'Accept':        'application/json',
        'Content-Type':  'application/json'
    }

    request = {
        'card_nonce': nonce,
        'note': ','.join([event.date.strftime('%Y-%m-%d'), event.name, driver.lastname, driver.firstname]),
        'amount_money': {
            'amount': int(amount*100),
            'currency': 'USD'
        },
        'buyer_email_address': driver.email,
        'billing_address': {
            'address_line_1': driver.attr.get('address', ''),
            'locality':       driver.attr.get('city', ''),
            'postal_code':    driver.attr.get('zip', ''),
            'country':        "US"   # FINISH ME, add country to driver?
        },
        'idempotency_key': str(uuid.uuid1())
    }

    url = '/v2/locations/{}/transactions'.format(account.accountid)
    connection = http.client.HTTPSConnection('connect.squareup.com')
    connection.request('POST', url, json.dumps(request), headers)
    response = json.loads(connection.getresponse().read())

    if "transaction" in response:
        p = Payment()
        p.txid      = response['transaction']['id']
        p.accountid = account.accountid
        p.driverid  = driver.driverid
        p.eventid   = event.eventid
        p.amount    = amount
        p.insert()
        return ""

    if "errors" in response:
        log.error("square payment error: {}".format(response['errors']))
        return ("Square reports: {}".format(response['errors'][0]['category']))

    log.error("Unknown response from square: {}".format(response))
    return ("Unknown response from Square")


def square_oauth_complete():
    """ Perform the second half of the oauth process """
    authorization_code = request.args.get('code', None)
    if not authorization_code:
        flash('Authorization Failed')
        return redirect(url_for('.accounts'))

    appid     = current_app.config.get('SQ_APPLICATION_ID', '')
    appsecret = current_app.config.get('SQ_APPLICATION_SECRET', '')
    if not appid or not appsecret:
        flash('There is no square applcation setup in the local configuration')
        return redirect(url_for('.accounts'))

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
        error = 'Code exchange failed: ' + str(response)
        log.warning(error)
        flash(error)
        return redirect(url_for('.accounts'))

    return response


def square_obtain_locations(access_token):
    """ Get the locations available with an access_token """
    oauth_headers = {
      'Authorization': 'Bearer '+access_token,
      'Accept':        'application/json',
      'Content-Type':  'application/json'
    }

    try:
        connection = http.client.HTTPSConnection('connect.squareup.com')
        connection.request('GET', '/v2/locations', '', oauth_headers)
        return json.loads(connection.getresponse().read())['locations']
    except Exception as e:
        flash('Business location lookup error: ' + str(e))
        log.warning("Square merchant name lookup error", exc_info=e)
        return redirect(url_for('.accounts'))


