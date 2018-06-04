# Very simple middleware to mitigate browser caching problems where
# Javascript/CSS/images get out of sync with the markup, as an
# alternative to fullblown static compressors/compilers/whatnots.
# Debugging is simple, as no extra files are written or changed.
#
# Dump this file in your project and enable it with something like
# this in your settings.py:
#
# MIDDLEWARE = [
#    ...
#    'modtimeurls.ModTimeUrlsMiddleware',
# ]
#
# As a bonus, with the middleware enabled in Django, one can instruct
# whatever is serving the static files to add a cache expiration far
# out in the future on files served with a _ GET parameter to enable
# all upstream caches including the browser to make as much use of the
# files as possible.
#
# For instance, for nginx, something like this:
#
#   location /static/ {
#     if ($args ~ "^_=") { expires 1y; }
#   }
#
# How it works:
#
# The middleware will search and replacing src="" and href="" in
# Django HTML responses to add ?_=<modification time> on links to
# files that reside in MEDIA_ROOT or STATIC_ROOT:
#
#  <img src="/media/foo.jpg"> -> <img src="/media/foo.jpg?_=432101234">
#  <script src="/static/bar.js"> -> <img src="/static/bar.js?_=78900987">
#
# The neat thing is that static file servers ignore the GET parameters
# when they are serving files, thus the modified URL still points to
# the same file but will change as soon as the file changes,
# alleviating problems with the markup and JS/images/CSS getting
# out of sync.
#
# By Ole Laursen, sponsored by IOLA, November 2010.
# - changed July 27, 2012 to add support for STATIC_ROOT
# - changed March 7, 2014 to fix missing HttpResponse content-type
# - changed March 28, 2014 to skip streaming responses.
# - changed December 12, 2017 to support new middleware interface in Django


import re, os

from django.conf import settings

url_attributes = ['src', 'href']

# stop matching when we hit <, > or " to guard against erratic markup
link_matcher = re.compile('((?:{})="(?:{}|{})[^<>"]*")'.format("|".join(url_attributes), re.escape(settings.STATIC_URL), re.escape(settings.MEDIA_URL)).encode("utf-8"))

def append_modtime_to_url(url):
    """Append the file modification time to URL if the URL is in
    STATIC_URL/MEDIA_URL and corresponds to a file in
    STATIC_ROOT/MEDIA_ROOT. This function can be used standalone in
    case there are links not catched by the middleware."""
    static = settings.STATIC_URL and settings.STATIC_ROOT and url.startswith(settings.STATIC_URL.encode("utf-8"))
    media = settings.MEDIA_URL and settings.STATIC_ROOT and url.startswith(settings.MEDIA_URL.encode("utf-8"))
    if not (static or media):
        return url

    if static:
        filename = os.path.join(settings.STATIC_ROOT.encode("utf-8"), url[len(settings.STATIC_URL.encode("utf-8")):])
    else:
        filename = os.path.join(settings.MEDIA_ROOT.encode("utf-8"), url[len(settings.MEDIA_URL.encode("utf-8")):])

    index = filename.rfind(b'?')
    contains_question_mark = index != -1
    
    if contains_question_mark:
        if filename[index:].find(b"_=") != -1: # url already has a _=, skip it
            return url

        filename = filename[:index]

    try:
        stat = os.stat(filename)
        timestamp = str(int(stat.st_mtime)).encode("utf-8")
        return url + (b'&' if contains_question_mark else b'?') + b"_=" + timestamp
    except OSError:
        pass

    return url

def append_modtime_to_urls_in_html(html):
    """Add modification time GET parameter to each media URL in input."""
    def replace_urls(m):
        before, url, after = m.group(1).split(b'"')

        return before + b'"' + append_modtime_to_url(url) + b'"' + after

    return link_matcher.sub(replace_urls, html)

def ModTimeUrlsMiddleware(get_response):
    """Middleware for adding modtime GET parameter to each media URL in responses."""

    def middleware(request):
        response = get_response(request)

        if response.has_header('content-type') and 'text/html' in response['content-type'].lower() and not getattr(response, "streaming", False):
            response.content = append_modtime_to_urls_in_html(response.content)
        return response

    return middleware
