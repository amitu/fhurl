from django.conf.urls.defaults import *
from django.http import HttpResponse
from django import forms
from fhurl import fhurl, RequestForm

class LoginFormWithoutRequest(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput)

    def save(self):
        return "/"

class LoginFormWithRequest(LoginFormWithoutRequest, RequestForm): pass

class FormWithHttpResponse(LoginFormWithRequest):
    def save(self):
        return HttpResponse("hi %s" % self.cleaned_data["username"])

urlpatterns = patterns('',
    fhurl(
        "^login/without/$", LoginFormWithoutRequest, template="login.html",
        pass_request=False
    ),
    fhurl("^login/with/$", LoginFormWithRequest, template="login.html"),
    fhurl("^with/http/$", FormWithHttpResponse, template="login.html"),
)
