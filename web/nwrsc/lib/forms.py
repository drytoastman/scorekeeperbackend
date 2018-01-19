import datetime
from functools import partial
import logging
from operator import attrgetter
import pytz

from flask import current_app, flash, request, url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DateTimeField, FieldList, FloatField, Form, FormField, HiddenField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField, IntegerField, URLField
from wtforms.validators import Email, InputRequired, Length, Optional, Required
from wtforms.widgets import TextInput

log = logging.getLogger(__name__)

def addlengthfields(field, kwargs):
    for v in field.validators:
        if isinstance(v, Length):
            if v.min > 0: kwargs.setdefault('minlength', field.validators[0].min)
            if v.max > 0: kwargs.setdefault('maxlength', field.validators[0].max)
            if v.min > 0 and v.max > 0: kwargs.setdefault('required', 1)
    return kwargs

def flashformerrors(form):
    for field,msg in form.errors.items():
        flash("{}: {}".format(field, msg[0]))

def none2Blank(val):
    if val is None: return ''
    return str(val)

class MyStringField(StringField):
    def __call__(self, **kwargs):
        return StringField.__call__(self, **addlengthfields(self, kwargs))

class MyPasswordField(PasswordField):
    def __call__(self, **kwargs):
        return PasswordField.__call__(self, **addlengthfields(self, kwargs))

class MyEmailField(EmailField):
    def __call__(self, **kwargs):
        kwargs.setdefault('required', 1)
        return EmailField.__call__(self, **kwargs)

class TZDateTimeField(DateTimeField):
    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        else:
            tz = pytz.timezone(current_app.config['UI_TIME_ZONE'])
            return self.data and self.data.astimezone(datetime.timezone.utc).astimezone(tz).strftime(self.format) or ''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                tz = pytz.timezone(current_app.config['UI_TIME_ZONE'])
                self.data = tz.localize(datetime.datetime.strptime(date_str, self.format)).astimezone(datetime.timezone.utc)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid datetime value'))


class BlankSelectField(SelectField):

    def iter_choices(self):
        yield ('__None', '', self.data is None)
        yield from SelectField.iter_choices(self)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] == '__None':
            self.data = None
        else:
            SelectField.process_formdata(self, valuelist)

    def pre_validate(self, form):
        if self.data is not None:
            SelectField.pre_validate(self, form)


class MyFlaskForm(FlaskForm):

    def html(self, idx, action, method, btnclass='btn-primary', labelcol='col-md-3', inputcol='col-md-9'):
        ret = list()
        ret.append("<form id='{}' action='{}' method='{}'>".format(idx, action, method))
        for f in self:
            if not hasattr(f.widget, 'input_type') or f.widget.input_type != 'submit':
                ret.append("<div class='row align-items-center'>")
                if not hasattr(f.widget, 'input_type') or f.widget.input_type != 'hidden':
                    if f.render_kw and 'labelextra' in f.render_kw:
                        ret.append("<div class='{} text-right'>{}<br/>{}</div>".format(labelcol, f.label(), f.render_kw['labelextra']))
                    else:
                        ret.append(f.label(class_=labelcol))
                ret.append(f(class_=inputcol))
                ret.append("</div>")

        ret.append("<div class='row'>")
        ret.append("<input type='checkbox' name='confirm' />")
        ret.append("</div>")

        ret.append("<div class='row'>")
        ret.append("<div class='{}'></div>".format(labelcol))
        ret.append(self.submit(class_="{} btn {}".format(inputcol, btnclass)))
        ret.append("</div>")
        ret.append("</form>")
        return '\n'.join(ret)

    def validate(self):
        if request.form.get('confirm'): # super simple bot test (advanced bots will get by this)
            log.warning("Suspect form submission from, ignoring: (%s)", request.form)
            abort(404)
        return FlaskForm.validate(self)


def formIntoAttrBase(form, base):
    """ Take form data and put into an AttrBase object """
    for k in base.columns:
        if hasattr(form, k):
            setattr(base, k, getattr(form, k).data)
    # leftover fields that aren't in the top level object
    ignore = set(base.columns + ['csrf_token', 'submit'])
    for k in set(form._fields) - ignore:
        base.attr[k] = getattr(form, k).data

def attrBaseIntoForm(base, form):
    """ Take AttrBase data and place it in form data """
    for k in base.columns:
        if hasattr(form, k):
            getattr(form, k).data = getattr(base, k)
    for k in base.attr:
        if hasattr(form, k):
            getattr(form, k).data = base.attr[k]


class SeriesPasswordForm(MyFlaskForm):
    password   = MyPasswordField('Password', [Length(min=2, max=32)])
    submit     = SubmitField(    'Login')

class PasswordForm(MyFlaskForm):
    gotoseries = HiddenField(    'gotoseries')
    username   = MyStringField(  'Username', [Length(min=6, max=32)])
    password   = MyPasswordField('Password', [Length(min=6, max=32)])
    submit     = SubmitField(    'Login')

class ResetForm(MyFlaskForm):
    firstname = MyStringField('First Name', [Length(min=2, max=32)])
    lastname  = MyStringField('Last Name',  [Length(min=2, max=32)])
    email     = MyEmailField( 'Email',     [Email()])
    submit    = SubmitField(  'Send Reset Information')

class RegisterForm(MyFlaskForm):
    gotoseries = HiddenField(   'gotoseries')
    firstname = MyStringField(  'First Name', [Length(min=2, max=32)])
    lastname  = MyStringField(  'Last Name',  [Length(min=2, max=32)])
    email     = MyEmailField(   'Email',     [Email()])
    username  = MyStringField(  'Username',  [Length(min=6, max=32)])
    password  = MyPasswordField('Password',  [Length(min=6, max=32)])
    submit    = SubmitField(    'Create New Profile')

class DriverForm(MyFlaskForm):
    driverid  = HiddenField(  'driverid')
    firstname = MyStringField('First Name', [Length(min=2, max=32)])
    lastname  = MyStringField('Last Name',  [Length(min=2, max=32)])
    email     = MyEmailField( 'Email',      [Email()])
    optoutmail= BooleanField( 'Do Not Contact', render_kw={'title':"Only use email address for password reset messages"})
    membership= MyStringField('Barcode',    [Length(max=16)])
    address   = MyStringField('Address',    [Length(max=64)])
    city      = MyStringField('City   ',    [Length(max=64)])
    state     = MyStringField('State',      [Length(max=16)])
    zip       = MyStringField('Zip',        [Length(max=8)])
    phone     = MyStringField('Phone',      [Length(max=16)])
    brag      = MyStringField('Brag',       [Length(max=64)])
    sponsor   = MyStringField('Sponsor',    [Length(max=64)])
    econtact  = MyStringField('Emerg Contact', [Length(max=64)])
    ephone    = MyStringField('Emerg Phone',   [Length(max=64)])
    submit    = SubmitField(  'Update')

class PasswordChangeForm(MyFlaskForm):
    driverid    = HiddenField(    'driverid')
    oldpassword = MyPasswordField('Current Password', [Length(min=6, max=32)])
    newpassword = MyPasswordField('New Password', [Length(min=6, max=32)])
    submit      = SubmitField(    'Change Password')


class CarForm(MyFlaskForm):
    driverid    = HiddenField(  'driverid')
    carid       = HiddenField(  'carid')
    year        = MyStringField('Year',  [Length(max=8)])
    make        = MyStringField('Make',  [Length(max=16)])
    model       = MyStringField('Model', [Length(max=16)])
    color       = MyStringField('Color', [Length(max=16)])
    classcode   = SelectField(  'Class', [Required()])
    indexcode   = SelectField(  'Index', coerce=none2Blank)
    useclsmult  = BooleanField( 'MultFlag')
    number      = IntegerField( 'Number', [Required()])
    submit      = SubmitField(  'Update')

    def __init__(self, classdata):
        MyFlaskForm.__init__(self)
        self.classcode.choices = [(c.classcode, "%s - %s" % (c.classcode, c.descrip)) for c in sorted(classdata.classlist.values(), key=attrgetter('classcode')) if c.classcode != 'HOLD']
        self.indexcode.choices = [(i.indexcode, "%s - %s" % (i.indexcode, i.descrip)) for i in sorted(classdata.indexlist.values(), key=attrgetter('indexcode'))]


class IndexForm(Form):
    indexcode   = MyStringField('IndexCode', [Length(min=2,max=8)], render_kw={'size':6})
    descrip     = MyStringField('Description',                      render_kw={'size':50})
    value       = FloatField(   'Value',                            render_kw={'size':5})

class IndexListForm(FlaskForm):
    indexlist   = FieldList(FormField(IndexForm))


class ClassForm(Form):
    classcode       = MyStringField('ClassCode', [Length(min=2,max=8)], render_kw={'title':"Required classcode", 'size':6})
    descrip         = MyStringField('Description',                      render_kw={'title':"A user description", 'size':50})
    eventtrophy     = BooleanField( 'Event Trophies',                   render_kw={'title':"Receives trophies at events"})
    champtrophy     = BooleanField( 'Champ Trophies',                   render_kw={'title':"Receives trophies for the series"})
    carindexed      = BooleanField( 'Cars Are Indexed',                 render_kw={'title':"Cars are individually indexed by index value"})
    secondruns      = BooleanField( 'Second Runs',                      render_kw={'title':"This class represents second entries for the day"})
    indexcode       = SelectField(  'ClassIndex',                       render_kw={'title':"Entire class is indexed by this index code"})
    classmultiplier = FloatField(   'ClassMultiplier',                  render_kw={'title':"This multiplier is applied to entire class, i.e. street tire factor", "size":3})
    usecarflag      = BooleanField( 'Use Car Flag',                     render_kw={'title':"Require that the car flag is checked for the additional multiplier to be applied"})
    caridxrestrict  = MyStringField('Restricted Index String')
    countedruns     = IntegerField( 'Counted Runs', widget=TextInput(), render_kw={'title':"Limit number of counted runs for this class", "size":2})

    def __init__(self, indexlist, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.indexcode.choices = [(i.indexcode, i.indexcode) for i in sorted(indexlist.values(), key=attrgetter('indexcode'))]

class ClassListForm(MyFlaskForm):
    @classmethod
    def setIndexes(cls, indexoptions):
        """ This is ugly as **** but its the only what I can get my choices to the internal form field, MAJOR reentry problems """
        """ At least its only used when administering classes so multiple use _should_ be limited """
        cls.classlist = FieldList(FormField(partial(ClassForm, indexoptions)))


class SettingsForm(MyFlaskForm):
    seriesname          = MyStringField('Series Name',        [Length(min=2, max=64)])
    largestcarnumber    = IntegerField( 'Largest Car Number', [Required()])
    minevents           = IntegerField( 'Min Events',         [InputRequired()])
    dropevents          = IntegerField( 'Drop X Events',      [InputRequired()])
    classinglink        = URLField(     'Classing Help Link',         render_kw={'title':"A URL link for classing help that appears when createing a new car"}) 
    usepospoints        = BooleanField( 'Use Position For Points',    render_kw={'title':"Use the finishing position for points rather than difference from first"})
    pospointlist        = MyStringField('Position Points',            render_kw={'title':"The points for each position, starting with first, the last value will repeat to fill remaining values"})
    indexafterpenalties = BooleanField( 'Index After Penalties',      render_kw={'title':"Perform indexes after applying penalties, rather than vice versa"})
    superuniquenumbers  = BooleanField( 'Series Wide Unique Numbers', render_kw={'title':"Required that new car number are unique across all classes, not just the class in use"})
    resultscss          = TextAreaField('Results CSS',                render_kw={'title':"Extra CSS that is injected into all of the results pages for this series", 'rows':4})
    resultsheader       = TextAreaField('Results Header',             render_kw={'title':"Jinja template code for the Event Results links",
                                                                                 'labelextra':"<a href='default?resultsheader'>Default If Blank</a>",  # can't use url_for as there is no context when its read
                                                                                 'rows':4 })
    cardtemplate        = TextAreaField('Card Template',              render_kw={'title':"If provided, the HTML template to use for HTML based card printing",
                                                                                 'labelextra':"<a href='default?cardtemplate'>Default If Blank</a><br/><a href='default?cards'>Wrapped In</a>",
                                                                                 'rows':4})
    submit              = SubmitField(  'Update')


class EventSettingsForm(MyFlaskForm):
    eventid       = HiddenField(  'eventid')
    name          = MyStringField('Event Name',  [Length(min=4, max=32)])
    date          = DateField(    'Event Date',             render_kw={'title':'The date of the event'})  
    regopened     = TZDateTimeField('Registration Opens',   render_kw={'title':'When registration should open'}, format='%Y-%m-%d %H:%M')
    regclosed     = TZDateTimeField('Registration Closes',  render_kw={'title':'When registration should close'}, format='%Y-%m-%d %H:%M')
    perlimit      = IntegerField( 'Per Driver Entry Limit', render_kw={'title':'Limit to the number of entries a single driver can register (0=nolimit)'})
    totlimit      = IntegerField( 'Total Entry Limit',      render_kw={'title':'The total limit for all registrations for the event (0=nolimit)'})
    accountid     = BlankSelectField('Payment Account')
    paymentreq    = BooleanField( 'Payment Required',       render_kw={'title':'Check this box to require payment for registration'})
    notes         = TextAreaField('Notes',                  render_kw={'title':'Notes for the event that show up on the registation page', 'rows':6})
    ispro         = BooleanField( 'Is A ProSolo',           render_kw={'title':'Check if this is a ProSolo style event'}) 
    ispractice    = BooleanField( 'Is A Practice',          render_kw={'title':'Check if this is a practice and not counted towards championship points'})
    location      = MyStringField('Location',               render_kw={'title':'The location of the event'})
    sponsor       = MyStringField('Sponsor',                render_kw={'title':'The event sponsor'})
    host          = MyStringField('Host',                   render_kw={'title':'The event host'})
    chair         = MyStringField('Chair',                  render_kw={'title':'The event chair'})
    sinlimit      = IntegerField( 'Singles Entry Limit',    render_kw={'title':'When allowing multiple entries, a limit to the number of individual people that can register (0=nolimit)'})
    courses       = IntegerField( 'Course Count',           render_kw={'title':'The number of courses in the event'})
    runs          = IntegerField( 'Run Count',              render_kw={'title':'The number of runs in the event'})    
    countedruns   = IntegerField( 'Runs Counted',           render_kw={'title':'The number of runs counted towards results (0=all)'})
    segments      = IntegerField( 'Segment Count',          render_kw={'title':'The number of segments on each course'})
    conepen       = FloatField(   'Cone Penalty',           render_kw={'title':'The penalty value for hitting a cone'})
    gatepen       = FloatField(   'Gate Penalty',           render_kw={'title':'The penalty value for missing a gate'})
    submit        = SubmitField(  'Update')

class SeriesForm(MyFlaskForm):
    name         = MyStringField(  'Series Name', [Length(min=6, max=12)])
    password     = MyPasswordField('Password',    [Length(min=4, max=12)])
    copysettings = BooleanField(   'Copy Settings')
    copyclasses  = BooleanField(   'Copy Classes/Indexes')
    copycars     = BooleanField(   'Copy Cars')
    submit       = SubmitField(    'Create')

class ArchiveForm(MyFlaskForm):
    name         = MyStringField(  'Enter Series Name', [Length(min=6, max=12)])
    submit       = SubmitField(    'Archive')

class PayPalAccountForm(MyFlaskForm):
    name       = MyStringField(  'Account Name', [Length(min=4)])
    accountid  = MyStringField(  'Client Id')
    secret     = MyStringField(  'Client Secret')
    submit     = SubmitField(    'Add PayPal Account')

class PaymentItemForm(MyFlaskForm):
    accountid  = HiddenField(  'accountid')
    name       = MyStringField('Item Name',      [Length(min=4)])
    price      = FloatField(   'Price')
    submit     = SubmitField(  'Add Item')

