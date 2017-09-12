from collections import defaultdict
from datetime import datetime, timedelta
import io
import logging
import operator
import psycopg2
import re

from flask import abort, Blueprint, current_app, flash, g, redirect, request, render_template, session, url_for

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
    if g.eventid:
        g.event=Event.get(g.eventid)
        if g.event is None:
            abort(404, "No such event")


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
    return render_template('/admin/event.html', event=g.event)

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


@Admin.route("/classlist", methods=['POST', 'GET'])
def classlist():
    classdata = ClassData.get()
    ClassListForm.setIndexes(classdata.indexlist)
    form = ClassListForm()
    if request.form:
        if form.validate():
            try:
                ClassData.get().updateClassesTo({k.data['classcode']:Class.fromForm(k.data) for k in form.classlist})
                return redirect(url_for('.classlist'))
            except psycopg2.IntegrityError as ie:
                flash("Unable to update classes: {}".format(ie))
            except Exception as e:
                flash("Exception processing classlist: {}".format(e))
                log.error("General exception processing classlist", exc_info=e)
        else:
            flashformerrors(form)
    else:
        classdata = ClassData.get()
        classdata.classlist.pop('HOLD', None)
        for key, cls in sorted(classdata.classlist.items()):
            form.classlist.append_entry(cls)

    return render_template('/admin/classlist.html', form=form)


@Admin.route("/indexlist", methods=['POST', 'GET'])
def indexlist():
    form = IndexListForm()
    if request.form:
        if form.validate():
            try:
                ClassData.get().updateIndexesTo({k.data['indexcode']:Index.fromForm(k.data) for k in form.indexlist})
                return redirect(url_for('.indexlist'))
            except psycopg2.IntegrityError as ie:
                flash("Unable to update indexes: {}".format(ie))
            except Exception as e:
                flash("Exception processing indexlist: {}".format(e))
                log.error("General exception processing indexlist", exc_info=e)
        else:
            flashformerrors(form)
    else:
        classdata = ClassData.get()
        classdata.indexlist.pop("", None)
        for key, idx in sorted(classdata.indexlist.items()):
            form.indexlist.append_entry(idx)

    return render_template('/admin/indexlist.html', form=form)


@Admin.route("/settings", methods=['POST', 'GET'])
def settings():
    form = SettingsForm()
    if request.form:
        if form.validate():
            newsettings = Settings.fromForm(form)
            newsettings.save()
            return redirect(url_for('.settings'))
        else:
            flashformerrors(form)
    else:
        form.process(obj=Settings.get())

    return render_template('/admin/settings.html', settings=settings, form=form)


@Admin.route("/event/<uuid:eventid>/edit", methods=['POST','GET'])
def eventedit():
    """ Process edit event form submission """
    form = EventSettingsForm()
    if request.form:
        if form.validate():
            newevent = Event()
            formIntoAttrBase(form, newevent)
            newevent.update()
            return redirect(url_for('.eventedit'))
        else:
            flashformerrors(form)
    else:
        attrBaseIntoForm(g.event, form)

    return render_template('/admin/eventedit.html', form=form, url=url_for('.eventedit'))


@Admin.route("/createevent", methods=['POST','GET'])
def createevent():
    """ Present form to create a new event """
    form = EventSettingsForm()
    if request.form:
        if form.validate():
            newevent = Event()
            formIntoAttrBase(form, newevent)
            newevent.insert()
            return redirect(url_for('.index'))
        else:
            flashformerrors(form)
    else:
        attrBaseIntoForm(Event.new(), form)

    return render_template('/admin/eventedit.html', form=form, url=url_for('.createevent'))


@Admin.route("/event/<uuid:eventid>/deleteevent")
def deleteevent():
    """ Request to delete an event, verify if we can first, then do it """
    try:
        g.event.delete()
        return redirect(url_for(".index"))
    except psycopg2.IntegrityError as ie:
        flash("Unable to delete event as its still referenced: {}".format(ie.diag.message_detail))
        return redirect(url_for(".event"))


@Admin.route("/event/<uuid:eventid>/list",        endpoint='list')
@Admin.route("/event/<uuid:eventid>/rungroups",   endpoint='rungroups')
@Admin.route("/event/<uuid:eventid>/previousattend", endpoint='previousattend')
@Admin.route("/drivers",     endpoint='drivers')
@Admin.route("/purge",       endpoint='purge')
@Admin.route("/newentrants", endpoint='newentrants')
@Admin.route("/contactlist", endpoint='contactlist')
@Admin.route("/copyseries",  endpoint='copyseries')
def notyetdone():
    return render_template('/admin/simple.html', text='This is TBD')


#####################################################################################################

class AdminController():

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
            return redirect(url_for(action='editor', name=name))

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
        return redirect(url_for(action='rungroups'))
        

    #@validate(schema=EventSchema(), form='createevent', prefix_error=False)
    def newevent(self):
        """ Process new event form submission """
        ev = Event(**self.form_result)
        self.session.add(ev)
        self.session.commit()
        return redirect(url_for(eventid=ev.id, action=''))


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
        return redirect(url_for(action='list'))
    

