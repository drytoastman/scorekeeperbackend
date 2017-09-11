from collections import defaultdict
from datetime import datetime, timedelta
import logging
import operator
import psycopg2
import re
import io

from flask import Blueprint, current_app, flash, g, redirect, request, render_template, session, url_for

from nwrsc.lib.forms import *
from nwrsc.model import *

log     = logging.getLogger(__name__)
Admin   = Blueprint("Admin", __name__)
AUTHKEY = 'adminauth'
PATHKEY = 'origpath'

def recordpath():
    if PATHKEY not in session[AUTHKEY]:
        session[AUTHKEY][PATHKEY] = request.path
        session.modified = True

def clearpath():
    if PATHKEY in session[AUTHKEY]:
        del session[AUTHKEY][PATHKEY]
        session.modified = True

@Admin.before_request
def setup():
    """ Every page underneath here requires a password """
    g.title = 'Scorekeeper Admin'
    log.debug("session is %s", session)
    if AUTHKEY not in session:
        session[AUTHKEY] = {}
    if not g.series in session[AUTHKEY]:
        recordpath()
        return login()
    
    clearpath()
    g.activeseries = Series.active()
    g.events  = Event.byDate()


@Admin.route("/login", methods=['POST', 'GET'])
def login():
    """ Assumes container db is named as such but it works, can't use config/unix socket as it implicitly trusts any user declaration """
    if request.form.get('password'):
        try:
            password = request.form.get('password')[:16].strip()
            psycopg2.connect(host='db', port=5432, user=g.series, password=password, dbname='scorekeeper').close()
            session[AUTHKEY][g.series] = 1
            session.modified = True
            return redirect(session[AUTHKEY][PATHKEY])
        except Exception as e:
            log.error("Login failure: %s", e, exc_info=e)
    return render_template('/admin/login.html')
    
@Admin.route("/")
def index():
    return render_template('/admin/status.html')

@Admin.route("/event/<uuid:eventid>")
def event():
    return render_template('/admin/event.html', event=Event.get(g.eventid))

@Admin.route("/numbers")
def numbers():
    numbers = defaultdict(lambda: defaultdict(set))
    settings = Settings.get()
    for res in NumberEntry.allNumbers():
        if settings.superuniquenumbers:
            res.code = "All"
        numbers[res.classcode][res.number].add(res.firstname+" "+res.lastname)
    return render_template('/admin/numberlist.html', numbers=numbers)

@Admin.route("/printhelp")
def printhelp():
    return render_template("/admin/printhelp.html")

@Admin.route("/restricthelp")
def restricthelp():
    return render_template('/admin/restricthelp.html')

def _multidecode(prefix):
    """ Decode form input of {prefix}-{index}.{key} = {value} array """
    objs = defaultdict(dict)
    for field, value in request.form.items():
        pre, idx, key = re.split('-|\.', field)
        if pre != prefix: continue
        objs[idx][key] = value
    return objs

@Admin.route("/classlist", methods=['POST', 'GET'])
def classlist():
    if request.form:
        try:
            objs = _multidecode('clslist')
            classes = {d['classcode']:Class.fromForm(d) for d in objs.values()}
            ClassData.get().updateClassesTo(classes)
        except psycopg2.IntegrityError as ie:
            flash("Unable to delete as class still in use: {}".format(ie.diag.message_detail))
        except Exception as e:
            flash("Exception processing classlist: {}".format(e))
            log.error("General exception processing classlist", exc_info=e)
        finally:
            redirect(url_for('.classlist'))

    classdata = ClassData.get()
    classdata.classlist.pop('HOLD', None)
    return render_template('/admin/classlist.html', classdata=classdata)
 
@Admin.route("/indexlist", methods=['POST', 'GET'])
def indexlist():
    if request.form:
        try:
            objs = _multidecode('clslist')
            indexes = {d['indexcode']:Index.fromForm(d) for d in objs.values()}
            ClassData.get().updateIndexesTo(indexes)
        except psycopg2.IntegrityError as ie:
            flash("Unable to delete as index still in use: {}".format(ie.diag.message_detail))
        except Exception as e:
            flash("Exception processing indexlist: {}".format(e))
            log.error("General exception processing indexlist", exc_info=e)
        finally:
            redirect(url_for('.indexlist'))

    classdata = ClassData.get()
    classdata.indexlist.pop("", None)
    return render_template('/admin/indexlist.html', classdata=classdata)


@Admin.route("/settings", methods=['POST', 'GET'])
def settings():
    form = SettingsForm()
    if request.form:
        if form.validate():
            settings = Settings.fromForm(form)
            settings.save()
        else:
            flashformerrors(form)
        redirect(url_for('.settings'))

    settings = Settings.get()
    form = SettingsForm(obj=settings)
    return render_template('/admin/settings.html', settings=settings, form=form)


@Admin.route("/event/<uuid:eventid>/edit", methods=['POST','GET'])
def eventedit():
    """ Process edit event form submission """
    form = EventSettingsForm()
    if request.form:
        if form.validate():
            event = Event()
            formIntoAttrBase(form, event)
            event.update()
        else:
            flashformerrors(form)
        redirect(url_for('.eventedit'))

    form = EventSettingsForm(obj=Event.get(g.eventid))
    return render_template('/admin/eventedit.html', form=form)


@Admin.route("/event/<uuid:eventid>/list",        endpoint='list')
@Admin.route("/event/<uuid:eventid>/rungroups",   endpoint='rungroups')
@Admin.route("/event/<uuid:eventid>/deleteevent", endpoint='deleteevent')
@Admin.route("/event/<uuid:eventid>/previousattend", endpoint='previousattend')
@Admin.route("/createevent", endpoint='createevent')
@Admin.route("/drivers",     endpoint='drivers')
@Admin.route("/purge",       endpoint='purge')
@Admin.route("/newentrants", endpoint='newentrants')
@Admin.route("/contactlist", endpoint='contactlist')
@Admin.route("/copyseries",  endpoint='copyseries')
def notyetdone():
    return render_template('/admin/simple.html', text='This is TBD')


#####################################################################################################

class AdminController():

    def _validateNumber(self, num):
        try:
            nummatch = re.compile('(\d{6}_\d)|(\d{6})')
            obj = nummatch.search(num)
        except:
            raise Exception("_validateNumber failed on the value '%s'" % num)
        if obj is not None:
            return obj.group(1) or obj.group(2)
        raise IndexError("nothing found")
    
    def contactlist(self):
        c.classlist = self.session.query(Class).order_by(Class.code).all()
        c.indexlist = [""] + [x[0] for x in self.session.query(Index.code).order_by(Index.code)]
        c.preselect = request.GET.get('preselect', "").split(',')

        c.drivers = dict()
        for (dr, car, reg) in self.session.query(Driver, Car, Registration).join('cars', 'registration'):
            if self.eventid.isdigit() and reg.eventid != int(self.eventid): 
                continue

            if dr.id not in c.drivers:
                dr.events = set([reg.eventid])
                dr.classes = set([car.classcode])
                c.drivers[dr.id] = dr
            else:
                dr = c.drivers[dr.id]
                dr.events.add(reg.eventid)
                dr.classes.add(car.classcode)

        if self.eventid.isdigit():
            c.title = c.event.name
            c.showevents = False
        else:
            c.title = "Series"
            c.showevents = True

        return render_template('/admin/contactlist.html')

    def downloadcontacts(self):
        """ Process settings form submission """
        idlist = request.POST['ids'].split(',')
        drivers = self.session.query(Driver).filter(Driver.id.in_(idlist)).all()
        cols = ['id', 'firstname', 'lastname', 'email', 'address', 'city', 'state', 'zip', 'phone', 'membership', 'brag', 'sponsor']
        return self.csv("ContactList", cols, drivers)

    ### Data editor ###
    def editor(self):
        if 'name' not in request.GET:
            return "Missing name"
        c.name = request.GET['name']
        c.data = ""
        data = self.session.query(Data).get(c.name)
        if data is not None:
            c.data = data.data
        return render_template('/admin/editor.html')

    def savecode(self):
        name = str(request.POST.get('name', None))
        data = str(request.POST.get('data', ''))
        if name is not None:
            Data.set(self.session, name, data)
            self.session.commit()
            redirect(url_for(action='editor', name=name))

    def paid(self):
        """ Return the list of fees paid before this event """
        c.header = '<h2>Fees Collected Before %s</h2>' % c.event.name
        c.beforelist = FeeList.get(self.session, self.eventid)[-1].before
        return render_template('/admin/feelist.html')

    def newentrants(self):
        """ Return the list of new entrants/fees collected by event or for the series """
        if self.eventid == 's':
            c.feelists = FeeList.getAll(self.session)
            return render_template('/admin/newentrants.html')
        else:
            c.feelists = FeeList.get(self.session, self.eventid)
            return render_template('/admin/newentrants.html')

    def paypal(self):
        """ Return a list of paypal transactions for the current event """
        c.payments = self.session.query(Payment).filter(Payment.eventid==self.eventid).all()
        c.payments.sort(key=lambda obj: obj.driver.lastname)
        return render_template('/admin/paypal.html')    

    ### RunGroup Editor ###
    def rungroups(self):
        c.action = 'setRunGroups'
        c.groups = {0:[]}
        allcodes = set([res[0] for res in self.session.query(Class.code)])
        for group in self.session.query(RunGroup).order_by(RunGroup.rungroup, RunGroup.gorder).filter(RunGroup.eventid==self.eventid).all():
            c.groups.setdefault(group.rungroup, list()).append(group.classcode)
            allcodes.discard(group.classcode)
        for code in sorted(allcodes):
            c.groups[0].append(code)
        return render_template('/admin/editrungroups.html')


    def setRunGroups(self):
        try:
            for group in self.session.query(RunGroup).filter(RunGroup.eventid==self.eventid):
                self.session.delete(group)
            self.session.flush()
            for k in request.POST:
                if k[:5] == 'group':
                    if int(k[5]) == 0:  # not recorded means group 0
                        continue
                    for ii, code in enumerate(request.POST[k].split(',')):
                        g = RunGroup()
                        g.eventid = self.eventid
                        g.rungroup = int(k[5])
                        g.classcode = str(code)
                        g.gorder = ii
                        self.session.add(g)
            self.session.commit()
        except Exception as e:
            log.error("setRunGroups failed: %s" % e)
            self.session.rollback()
        redirect(url_for(action='rungroups'))
        

    def createevent(self):
        """ Present form to create a new event """
        c.action = 'newevent'
        c.button = 'New'
        c.event = Event()
        c.event.conepen = 2.0
        c.event.gatepen = 10.0
        c.event.courses = 1
        c.event.runs = 4
        c.event.perlimit = 2
        c.event.totlimit = 0
        c.event.doublespecial = False
        c.event.date = datetime.today()
        c.event.regopened = datetime.today()
        c.event.regclosed = datetime.today()
        return render_template('/admin/eventedit.html')

    #@validate(schema=EventSchema(), form='createevent', prefix_error=False)
    def newevent(self):
        """ Process new event form submission """
        ev = Event(**self.form_result)
        self.session.add(ev)
        self.session.commit()
        redirect(url_for(eventid=ev.id, action=''))


    def deleteevent(self):
        """ Request to delete an event, verify if we can first, then do it """
        if self.session.query(Run).filter(Run.eventid==self.eventid).count() > 0:
            c.text = "<h3>%s has runs assigned to it, you cannot delete it</h3>" % (c.event.name)
            raise BeforePage(render_template('/admin/simple.html'))

        # no runs, kill it
        self.session.query(Registration).filter(Registration.eventid==self.eventid).delete()
        self.session.query(Event).filter(Event.id==self.eventid).delete()
        self.session.commit()
        redirect(url_for(eventid='s', action=''))


    def list(self):
        query = self.session.query(Driver,Car,Registration).join('cars', 'registration').filter(Registration.eventid==self.eventid)
        c.classdata = ClassData(self.session)
        c.registered = {}
        for (driver, car, reg) in query.all():
            if car.classcode not in c.registered:
                c.registered[car.classcode] = []
            c.registered[car.classcode].append(RegObj(driver, car, reg))
        return render_template('/admin/entrylist.html')

    def delreg(self):
        regid = request.POST.get('regid', None)
        if regid:
            reg = self.session.query(Registration).filter(Registration.id==regid).first()
            if reg:
                self.session.delete(reg)
                self.session.commit()
        redirect(url_for(action='list'))
    

