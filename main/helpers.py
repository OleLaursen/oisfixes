from django.shortcuts import render

class Page(object):
    def __init__(self):
        self.js = ["common.js"]
        self.css = ["global.css"]

def render_page(request):
    return render(request, "base.html", dict(request=request))
