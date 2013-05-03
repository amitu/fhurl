# {{{
import sys
import json
import urllib
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.urlresolvers import get_mod_func
from django.utils.functional import Promise
from django.template import RequestContext
from datetime import datetime, date
from django.conf import settings
from django import forms
from smarturls import surl

if sys.version_info < (3,):
    try:
        from django.utils.translation import force_unicode
    except ImportError:
        from django.utils.encoding import force_unicode
    from urllib import quote as urlquote
else:
    # In Python 3 force_unicode does not exist for Django 1.5
    force_unicode = lambda text: text
    basestring = str
    from urllib.parse import quote as urlquote
# }}}

# JSONEncoder # {{{ 
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        else:
            return super(JSONEncoder, self).default(o)
# }}} 

# JSONResponse # {{{
class JSONResponse(HttpResponse):
    def __init__(self, data):
        HttpResponse.__init__(
            self, content=json.dumps(data, cls=JSONEncoder),
            content_type="application/json"
        ) 
# }}}

# get_form_representation # {{{
def get_form_representation(form):
    d = {}
    for field in form.fields:
        value = form.fields[field]
        dd = {}
        if value.label:
            dd["label"] = value.label.title()
        dd["help_text"] = value.help_text
        dd["required"] = value.required
        if field in form.initial:
            dd["initial"] = form.initial[field]
        if value.initial: dd["initial"] = value.initial
        d[field] = dd
    return d
# }}}

# RequestForm # {{{
class RequestForm(forms.Form):
    def __init__(self, request, *args, **kw):
        super(RequestForm, self).__init__(*args, **kw)
        self.request = request

    def get_json(self, saved):
        if hasattr(self, "obj"):
            if hasattr(self.obj, "get_json"):
                return self.obj.get_json()
            return self.obj
        if hasattr(saved, "get_json"):
            return saved.get_json()
        return saved

    def initialize(self, field=None, value=None, **kw):
        if field: self.fields[field].initial = value
        for k, v in kw.items():
            self.fields[k].initial = v
        return self

    def initialize_with_object(self, obj, *fields, **kw):
        for field in fields:
            self.fields[field].initial = getattr(obj, field)
        for ffield,ofield in kw.items():
            self.fields[ffield].initial = getattr(obj, ofield)
        return self

    def update_object(self, obj, *args, **kw):
        d = self.cleaned_data.get
        for arg in args:
            setattr(obj, arg, d(arg))
        for k, v in kw.items():
            setattr(obj, k, d(v))
        return obj
# }}}

class ResponseReady(Exception):
    def __init__(self, response, *args, **kw):
        self.response = response
        super(ResponseReady, self).__init__(*args, **kw)

# form_handler # {{{
def _form_handler(
    request, form_cls, require_login=False, block_get=False, ajax=False,
    next=None, template=None, login_url=None, pass_request=True,
    validate_only=False, **kwargs
):
    """
    Some ajax heavy apps require a lot of views that are merely a wrapper
    around the form. This generic view can be used for them.
    """
    if "next" in request.REQUEST: next = request.REQUEST["next"]
    from django.shortcuts import render_to_response
    is_ajax = request.is_ajax() or ajax or request.REQUEST.get("json")=="true"
    if isinstance(form_cls, basestring):
        # can take form_cls of the form: "project.app.forms.FormName"
        mod_name, form_name = get_mod_func(form_cls)
        form_cls = getattr(__import__(mod_name, {}, {}, ['']), form_name)
    validate_only = (
        validate_only or request.REQUEST.get("validate_only") == "true"
    )
    if login_url is None:
        login_url = getattr(settings, "LOGIN_URL", "/login/")
    if callable(require_login): 
        require_login = require_login(request)
    elif require_login:
        require_login = not request.user.is_authenticated()
    if require_login:
        redirect_url = "%s?next=%s" % (
            login_url, urlquote(request.get_full_path())
        ) # FIXME
        if is_ajax:
            return JSONResponse({ 'success': False, 'redirect': redirect_url })
        return HttpResponseRedirect(redirect_url)
    if block_get and request.method != "POST":
        raise Http404("only post allowed")
    if next: assert template, "template required when next provided"
    def get_form(with_data=False):
        form = form_cls(request) if pass_request else form_cls()
        form.next = next
        if with_data:
            form.data = request.REQUEST
            form.files = request.FILES
            form.is_bound = True
        if hasattr(form, "init"):
            res = form.init(**kwargs)
            if res: raise ResponseReady(res)
        return form
    if is_ajax and request.method == "GET":
        return JSONResponse(get_form_representation(get_form()))
    if template and request.method == "GET":
        return render_to_response(
            template, {"form": get_form()},
            context_instance=RequestContext(request)
        )
    form = get_form(with_data=True)
    if form.is_valid():
        if validate_only:
            return JSONResponse({"valid": True, "errors": {}})
        r = form.save()
        if is_ajax: return JSONResponse(
            {
                'success': True,
                'response': (
                    form.get_json(r) if hasattr(form, "get_json") else r
                )
            }
        )
        if isinstance(r, HttpResponse): return r
        if next: return HttpResponseRedirect(next)
        if template: return HttpResponseRedirect(r)
        return JSONResponse(
            {
                'success': True,
                'response': (
                    form.get_json(r) if hasattr(form, "get_json") else r
                )
            }
        )
    if validate_only:
        if "field" in request.REQUEST:
            errors = form.errors.get(request.REQUEST["field"], "")
            if errors: errors = "".join(errors)
        else:
            errors = form.errors
        return JSONResponse({ "errors": errors, "valid": not errors})
    if is_ajax:
        return JSONResponse({ 'success': False, 'errors': form.errors })
    if template:
        return render_to_response(
            template, {"form": form}, context_instance=RequestContext(request)
        )
    return JSONResponse({ 'success': False, 'errors': form.errors })
# }}}

def form_handler(*args, **kw):
    try:
        return _form_handler(*args, **kw)
    except ResponseReady as e:
        return e.response

# fhurl # {{{
def fhurl(reg, form_cls, decorator=lambda x: x, **kw):
    name = kw.pop("name", None)
    kw["form_cls"] = form_cls
    return surl(reg, decorator(form_handler), kw, name=name)
# }}}

# try_del # {{{ 
def try_del(d, *args):
    for f in args:
        try:
            del d[f]
        except KeyError: pass
    return d
# }}} 
