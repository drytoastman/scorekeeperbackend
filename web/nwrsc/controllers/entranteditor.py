import logging
import re
import uuid

from flask import g, make_response, render_template, request

from nwrsc.controllers.admin import Admin
from nwrsc.lib.encoding import json_encode
from nwrsc.model import *

log = logging.getLogger(__name__)

DIRECTIONS = re.compile(r'\s(Ne|Se|Sw|Nw)')

def titlecase(text, key):
    if key == 'state' and len(text) < 3:
        return text.upper()
    if key == 'address':
        return DIRECTIONS.sub(lambda pat: " " + pat.group(1).upper(), string.capwords(text))
    return string.capwords(text)

class DriverInfo(object):
    def __init__(self, d, c):
        self.driver = d
        self.cars = c
        # Make no values into blank strings
        for k, v in self.driver.__dict__.iteritems(): 
            if v is None:
                setattr(self.driver, k, "")
        for car in self.cars:
            for k, v in car.__dict__.iteritems(): 
                if v is None:
                    setattr(car, k, "")

@Admin.route("/drivers")
def drivers():
    return render_template('/admin/drivers.html')

@Admin.route("/getdrivers")
def getdrivers():
    return json_encode(Driver.getAll())

@Admin.route("/getitems/<uuid:driverid>")
def getitems(driverid):
    cars = Car.getForDriver(driverid)
    return json_encode(cars)

def mergedriver(self):
    try:
        driverid = int(request.POST.get('driverid', None))
        allids = map(int, request.POST.get('allids', '').split(','))
        allids.remove(driverid)
        for tomerge in allids:
            log.info("merge %s into %s" % (tomerge, driverid))
            # update car id maps
            for car in self.session.query(Car).filter(Car.driverid==tomerge):
                car.driverid = driverid 
            # delete old driver
            dr = self.session.query(Driver).filter(Driver.id==tomerge).first()
            self.session.delete(dr)
            
        self.session.commit()
        return "";
    except Exception as e:
        log.info('merge driver failed: %s' % e)
        abort(400);


def deletedriver(self):
    try:
        driverid = request.POST.get('driverid', None)
        log.info('request to delete driver %s' % driverid)
        for car in self.session.query(Car).filter(Car.driverid==driverid):
            if len(self.session.query(Run.eventid).distinct().filter(Run.carid==car.id).all()) > 0:
                raise Exception("driver car has runs")
            self.session.delete(car)
        dr = self.session.query(Driver).filter(Driver.id==driverid).first()
        self.session.delete(dr)
        self.session.commit()
        return "";
    except Exception as e:
        log.info('delete driver failed: %s' % e)
        abort(400);


def titlecasedriver(self):
    try:
        driverid = request.POST.get('driverid', None)
        log.info('request to titlecase driver %s' % driverid)
        dr = self.session.query(Driver).get(driverid)
        for attr in ('firstname', 'lastname', 'address', 'city', 'state'):
            setattr(dr, attr, titlecase(getattr(dr, attr), attr))
        self.session.commit()
        return "";
    except Exception as e:
        log.info('title case driver failed: %s' % e)
        abort(400);

def titlecasecar(self):
    try:
        carid = request.POST.get('carid', None)
        log.info('request to titlecase car %s' % carid)
        car = self.session.query(Car).get(carid)
        for attr in ('make', 'model', 'color'):
            setattr(car, attr, titlecase(getattr(car, attr), attr))
        self.session.commit()
        return "";
    except Exception as e:
        log.info('title case car failed: %s' % e)
        abort(400);


