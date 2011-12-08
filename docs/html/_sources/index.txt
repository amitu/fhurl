Django Generic Form Handler View -- fhurl
*****************************************

`fhurl.form_handler` is a generic view that can be used for handling
forms.

Install fhurl using::

    $ easy_install fhurl

fhurl is being developed on http://github.com/amitu/fhurl/.

See the Changelog: https://github.com/amitu/fhurl/blob/master/ChangeLog.rst.

form_handler
------------

.. function:: fhurl.form_handler(request, form_cls, require_login=False, block_get=False, next=None, template=None, login_url=None, pass_request=True, ajax=False, validate_only=False)

    Some ajax heavy apps require a lot of views that are merely a wrapper
    around the form. This generic view can be used for them.

    :param request: request object, instance of HttpRequest
    :param form_cls: form class to use
    :type form_cls: string or instance of Form subclass.
    :param require_login: boolean or callable, if this is true, use must login
        before they can interact with the form
    :param block_get: if true, GET requests are not allowed.
    :param next: if passed, user will be redirected to this url after success
    :param template: if passed, this template will be used to render form
    :param login_url: user will be redirected to this user if login is required
    :param pass_request: form instance would be created with request as first
        parameter if this is true
    :param ajax: if this is true, form_handler will only return JSON data
    :param validate_only: if this is true, form_handler will only validate
        fields and wont call form.save()
    :rtype: instance of HttpResponse subclass


fhurl
-----

.. function:: fhurl.fhurl(reg, form_cls, decorator=labmda x: x, \**kw)

    This is a utility function to be used in urls.py for convenience.

    :param reg: regular expression as used in django urls.
    :param form_cls: The form class to use.
    :type form_cls: string or django.forms.Form subclass.
    :param decorator: the decorator to use, optional.
    :param kw: rest of the keyword arguments as described above.

`form_handler` and `fhurl` can be used in various scenarios.

Simple Form Handling
--------------------

A typical form handler in django is the following view::

    from myproj.myapp.forms import MyForm

    def my_form_view(request):
        if request.method == "POST":
            form = MyForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect("/somewhere/")
        else:
            form = MyForm()
        return render_to_response(
            "my_form.html", { "form": form },
            context_instance=RequestContext(request)
        )

This can be handled by `fhurl` by putting the following entries in
urls.py::

    from django.conf.urls.defaults import *
    from fhurl import fhurl

    urlpatterns = patterns('',
        fhurl(
           r'^my-form/$', "myproj.myapp.forms.MyForm", template='my_form.html',
           next="/somewhere/", pass_request=False
        ),
    )

The URL To Be Redirected Is Variable
------------------------------------

Sometimes when lets say you created a new object, and user should be redirected
to that object, instead of a static url, `next` parameter is not suffecient. In
such cases, do not pass `next` and let form.save() return the URL.
`form_handler` will redirect user to this url.::

    class CreateBookForm(forms.Form):
        title = forms.CharField(max_length=50)

        def save(self):
            book = Book.objects.create(title=title)
            return book.get_absolute_url()

    urlpatterns = patterns('',
        fhurl(
            r'^create-book/$', CreateBookForm, template='create-book.html',
            pass_request=False,
        ),
    )

Access To Request Parameters Required
-------------------------------------

Sometimes for valid form processing, some aspect of request has to be know. In
this case make sure your Form constructore can take request as the first
parameter, and set `pass_request` to `True`.::


    class CreateBookForm(forms.Form):
        title = forms.CharField(max_length=50)

        def __init__(self, request, *args, **kw):
            super(CreateBookForm, self).__init__(*args, **kw)
            self.request = request

        def save(self):
            book = Book.objects.create(title=title, user=self.request.user)
            return book.get_absolute_url()

    urlpatterns = patterns('',
        fhurl(
            r'^create-book/$', CreateBookForm,
            template='create-book.html', require_login=True,
        ),
    )


fhurl comes with a utility class derived from Form known as `RequestForm`.
This form takes care of storing the request passed in constructor, so the above
form can be re written as::

    class CreateBookForm(fhurl.RequestForm):
        title = forms.CharField(max_length=50)

        def save(self):
            book = Book.objects.create(title=title, user=self.request.user)
            return book.get_absolute_url()

    urlpatterns = patterns('',
        fhurl(r'^create-book/$', CreateBookForm, template='create-book.html'),
    )


Only Users With Valid Account Can Access The Form
-------------------------------------------------

Sometimes being logged in is not enough, you may want users to satisfy some
kind of condition before they can access the form, for example their account is
valid, or it has enough balance or whatever.

This can be achieved by a combination of `require_login` and `login_url`. Lets
say our user object has can_create_books() method on its UserProfile.

Also lets assume that "/make-payment/" is the URL user will go to if they do
not have permission to create books.

Here is how to handle this situation::

    def can_create_books(request):
        if not request.user.is_authenticated(): return False
        return request.user.get_profile().can_create_books()

    urlpatterns = patterns('',
        fhurl(
            r'^create-book/$', CreateBookForm, login_url="/make-payment/",
            template='create-book.html', require_login=can_create_books,
        ),
    )

.. note::

    `require_login` can be a callable. If its a callable, it will be passed
    request as the first parameter.

.. note::

    In this example, make sure that /make-payment/ redirects user to /login/ if
    user is not logged in.

Forms That Take Parameters From URL
-----------------------------------

Django websites usually have clean URLs, which means no "/edit-book/?id=123",
rather "/book/123/edit/". We have to handle cases where data is coming from
URLs, instead of request parameters, to initialize the form.

For this use case `form_handler` requires forms with `.init()` method.

Consider the original view::

    @login_required
    def edit_book(request, book_id):
        book = get_object_or_404(Book, id=book_id)
        if not book.user == request.user:
             Http404
        if request.method == "POST":
            form = BookEditForm(book, request.POST)
            if form.is_valid():
                form.save()
                return book.get_absolute_url()
        else:
            form = BookEditForm(book)
        return render_to_response(
            "edit-book.html", {"form": form, "book": book},
            context_instance=RequestContext(request)
        )

With urls.py containing::

    from django.conf.urls.defaults import *

    urlpatterns = patterns('',
        # other urls
        url(r'^book/(?P<book_id>[\d]+)/edit/$', "myproj.myapp.view.edit_book")
    )

And forms.py with something like::

    from django import forms

    class BookEditForm(forms.Form):
        title = forms.CharField(max_length=50)

        def __init__(self, book, *args, **kw):
            super(BookEditForm, self).__init__(*args, **kw)
            self.book = book
            self.fields["title"].initial = book.title

        def save(self):
            self.book.title = self.cleaned_data["title"]
            self.book.save()

To handle this define .init() on BookEditForm, and put the view logic for
loading the book and doing validation in it::

    from django import forms

    class BookEditForm(fhurl.RequestForm):
        title = forms.CharField(max_length=50)

        def init(self, book_id):
            self.book = get_object_or_404(Book, id=book_id)
            if not self.book.user == self.request.user:
                Http404
            self.fields["title"].initial = self.book.title

        def save(self):
            self.book.title = self.cleaned_data["title"]
            self.book.save()

We do not need the view now, and use the form_handler like so::

    urlpatterns = patterns('',
        fhurl(
            r'^book/(?P<book_id>[\d]+)/edit/$', BookEditForm, 
            template="edit-book.html", require_login=True
        )
    )

`form_handler` will detect that the form has .init(), so it will call it. The
extra argument passed from the url, `book_id`, will be passed to .init() as
keyword argument.

.. note::

    Note that if .init() returns something, it is returned directly to users,
    which means, init() can perform all kinds of checks, and redirect users to
    different portions of site if required.

Doing Ajax
----------

Lets say we want to export all this as ajax. You actually don't have to do
anything, just pass "json=true" as a REQUEST parameter. You don't even have to
do that if request is coming from a browser with proper headers, as required by
`is_ajax
<http://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.is_ajax>`_.

.. code-block:: sh

    $ curl -d "username=newf&field=username&json=true" "http://localhost:8000/register/"
    {"errors": {"password1": ["This field is required."], "email": ["This field is required."]}, "success": false}

The form will return JSON objects, with parameter `success` which is `true` or
`false`.

If its `true` when everything goes well, in this case, it will contain
`response` parameter, which will be JSON encoded value of whatever was returned
by the `form.save()`.

`success` is `false` if there was some form validation error, or if redirect is
required. If redirect is required when conditions are not met, JSON contains a
parameter `redirect` which contains the URL to which user has to be redirected.

If `success` is `false` because of form validation errors, a property `errors`
contains JSON encoded error messages.

.. note::

    In ajax mode, if a GET request is made, a JSON representation of form is
    returned, containing initial values, lables, help_text etc. This can be
    used to auto generate form, or to get initial values etc.

A jquery plugin for fhurl forms:

.. code-block:: javascript

    $.fn.handle_form = function(cb) {
        return this.unbind("submit").submit(function(e){
            e.preventDefault()
            var form = this
            var $form = $(this)
            $.post(form.action, $form.serialize(), function(d){
                if (d.success) {
                    if(cb) cb(d.response)
                } else {
                    $(".error", form).empty()
                    $.each(d.errors, function(item, key){
                        $("#error_" + key).append("<li>" + item + "</li>")
                    })
                }
            }, "json")
        })
    }


Using Same Form For JSON Access And Normal Web Access
-----------------------------------------------------

Sometimes implicit conversion of object returned by form.save() can be limiting
in scenarios where same form is being used both for ajax handling and as normal
webform. 

Eg, /create-book/ when accessed via browser would want to return user to the
newly created book's permalink on success, while when the same URL is invoked
through ajax, we want to return the JSON representation of the book.

To handle this, give your form a .get_json() method, which when available is
called, and its output is returned to user for ajax invocation, and .save() can
safely return the permalink of the book, which will lead to browser getting
redirected to that user.

Eg::

    class CreateBook(fhurl.RequestForm):
        # fields
        # validation

        def get_json(self, saved):
            return self.book.__dict__ # gets JSONified for JSON calls

        def save(self):
            self.book = create_book(self.cleaned_data)
            return self.book.get_absolute_url() # browser gets redirected here

As You Type AJAX Validation
---------------------------

`form_handler` can be used for validating partially filled forms for as you
type validation of web forms.

This feature can be setup either on the URL basis by passing `validate_only` to
`form_handler` in `urls.py`, or on a per request basis by passing
`validate_only` request parameter.

If its being done on request basis, no setup is required, just pass the
`validate_only` parameter:

.. code-block:: sh

    $ curl -d "validate_only=true&username=&field=username" "http://localhost:8000/register/"
    {"errors": "This field is required.", "valid": false}
    $ curl -d "validate_only=true&username=amitu&field=username" "http://localhost:8000/register/"
    {"errors": "This username is already taken. Please choose another.", "valid": false}
    $ curl -d "validate_only=true&username=newf&field=username" "http://localhost:8000/register/"
    {"errors": "", "valid": true}

Some javascript to handle it:

.. code-block:: javascript

    $(function(){
        $("#id_username, #id_password, #id_password2, #id_email").blur(function(){
            var url = "/register/?validate_only=true&field=" + this.name;
            var field = this.name;
            $.ajax({
                url: url, data: $("#registration_form").serialize(),
                type: "post", dataType: "json",    
                success: function (response){ 
                    if(response.valid)
                    {
                        $("#"+field+"_errors").html("Sounds good");
                    }
                    else
                    {
                        $("#"+field+"_errors").html(response.errors);
                    }
                }
            });
        });
    });

