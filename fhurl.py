# {{{
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.translation import force_unicode
from django.core.urlresolvers import get_mod_func
from django.utils.functional import Promise
from django.template import RequestContext
from django.conf.urls.defaults import url
from datetime import datetime, date
from django.conf import settings
from django import forms
import json
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
            #mimetype="text/html",
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

# form_handler # {{{
def form_handler(
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
    elif isinstance(form_cls, dict):
        for k, v in form_cls.items():
            if not isinstance(v, basestring): continue
            mod_name, form_name = get_mod_func(v)
            form_cls[k] = getattr(__import__(mod_name, {}, {}, ['']), form_name)
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
        if require_login == "404":
            raise Http404("login required")
        redirect_url = "%s?next=%s" % (login_url, request.path) # FIXME
        if is_ajax:
            return JSONResponse({ 'success': False, 'redirect': redirect_url })
        return HttpResponseRedirect(redirect_url)
    if block_get and request.method != "POST":
        raise Http404("only post allowed")
    if next: assert template, "template required when next provided"
    def get_form(with_data=False):
        # TODO: allow defaults from URL?
        if isinstance(form_cls, dict):
            assert "fh_form" in request.REQUEST
            form = form_cls[request.REQUEST["fh_form"]]
            forms = form_cls
            for k, f in forms.items():
                forms[k] = f(request) if pass_request else f()
        else:
            form = form_cls(request) if pass_request else form_cls()
            forms = { "form": form }
        if with_data:
            form.data = request.REQUEST
            form.files = request.FILES
            form.is_bound = True
        for f in forms.values():
            if hasattr(f, "init"):
                res = f.init(**kwargs)
                if res: return res
        return form, forms
    if is_ajax and request.method == "GET":
        return JSONResponse(get_form_representation(get_form()[0]))
    if template and request.method == "GET":
        return render_to_response(
            template, get_form()[1],
            context_instance=RequestContext(request)
        )
    form, forms = get_form(with_data=True)
    if form.is_valid():
        if validate_only:
            return JSONResponse({"valid": True, "errors": {}})
        r = form.save()
        if isinstance(r, HttpResponse): return r
        if is_ajax: return JSONResponse(
            {
                'success': True,
                'response': (
                    form.get_json(r) if hasattr(form, "get_json") else r
                )
            }
        )
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
            template, forms, context_instance=RequestContext(request)
        )
    return JSONResponse({ 'success': False, 'errors': form.errors })
# }}}

# fhurl # {{{
def fhurl(reg, form_cls, decorator=lambda x: x, **kw):
    name = kw.pop("name", None)
    kw["form_cls"] = form_cls
    return url(reg, decorator(form_handler), kw, name=name)
# }}}

# try_del # {{{ 
def try_del(d, *args):
    for f in args:
        try:
            del d[f]
        except KeyError: pass
    return d
# }}} 
