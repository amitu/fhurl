"""
>>> from django.test.client import Client
>>> import json
>>> c = Client()
>>>

>>> r = c.get("/login/with/")
>>> r.status_code
200
>>> r.templates[0].name
'login.html'
>>> 'This field is required.' in r.content
False

>>> r = c.post("/login/with/")
>>> r.status_code
200
>>> r.templates[0].name
'login.html'
>>> len(r.content.split("This field is required."))
3

>>> r = c.post("/login/with/", {"username": "john"})
>>> r.status_code
200
>>> len(r.content.split("This field is required."))
2

>>> good_data = {"username": "john", "password": "asd"}

>>> r = c.post("/login/with/", good_data)
>>> r.status_code
302
>>> r.content
''
>>> r["Location"]
'http://testserver/'

>>> r = c.get("/login/without/")
>>> r.status_code
200
>>> r.templates[0].name
'login.html'
>>> 'This field is required.' in r.content
False

>>> r = c.post("/login/without/")
>>> r.status_code
200
>>> r.templates[0].name
'login.html'
>>> len(r.content.split("This field is required."))
3

>>> r = c.post("/login/without/", {"username": "john"})
>>> r.status_code
200
>>> len(r.content.split("This field is required."))
2

>>> r = c.post("/login/without/", good_data)
>>> r.status_code
302
>>> r.content
''
>>> r["Location"]
'http://testserver/'


>>> r = c.get("/with/http/")
>>> r.status_code
200
>>> r.templates[0].name
'login.html'

>>> r = c.post("/with/http/", good_data)
>>> r.status_code
200
>>> r.content
'hi john'


>>> r = c.get("/with/variable/redirect/")
>>> r.status_code
200
>>> r.templates[0].name
'login.html'

>>> r = c.post("/with/variable/redirect/", good_data)
>>> r.status_code
302
>>> r["location"]
'http://testserver/john/'

>>> r = c.get("/with/data/jack/")
>>> r.status_code
200
>>> 'value="jack"' in r.content
True


##### Init returning response feature is not working ########
#>>> r = c.get("/init/returning/jack/")
#>>> r.status_code
#200

#>>> r.content
#'good boy jack'

##### Init raising 404 feature is not working ########
#>>> r = c.get("/init/raising/404/")
#>>> r.status_code
#404

>>> r = c.get("/login/required/")
>>> r.status_code
302
>>> r["Location"]
'http://testserver/accounts/login/?next=/login/required/'


>>> r = c.get("/login/required/with/url/")
>>> r.status_code
302
>>> r["Location"]
'http://testserver/mylogin/?next=/login/required/with/url/'




"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()
