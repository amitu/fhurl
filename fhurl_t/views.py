from django.http import HttpResponse

def session_test(request):
    request.session.setdefault("count", 0)
    request.session["count"] += 1
    return HttpResponse("session: %s" % request.session["count"])
