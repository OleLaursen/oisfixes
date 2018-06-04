# Simple middleware to search and replacing src="" and href="" in HTML
# responses to add ?_=<modification time> on links to files that
# reside in MEDIA_ROOT:
#
#  <img src="/media/foo.jpg"> -> <img src="/media/foo.jpg?_=432101234">
#
# The neat thing is that static file servers ignore the GET parameters
# when they are serving files, thus the modified URL still points to
# the same file but will change as soon as the file changes,
# alleviating problems with the markup and scripts/images/CSS getting
# out of sync.
#
# Dump this file in your project and enable it with something like
# this in your settings.py:
#
# MIDDLEWARE_CLASSES = (
#    ...
#    'modtimeurls.ModTimeUrlsMiddleware',
#    )
#
# As a bonus, with the middleware enabled in Django, one can instruct
# whatever is serving the static files to add a cache expiration far
# out in the future on files served with a _ GET parameter to enable
# all upstream caches including the browser to make as much use of the
# files as possible.
#
# For instance, for lighttpd, something like this can be used:
#
#   $HTTP["querystring"] =~ "^_=" { expire.url = ( "" => "access 1 years") }
#
# For nginx, something like this:
#
#   location /media/ {
#     if ($args ~ "^_=") { expires 1y; }
#   }
#
# By Ole Laursen, sponsored by IOLA, November 2010.


import re, os

from django.conf import settings

url_attributes = ['src', 'href']

# stop matching when we hit <, > or " to guard against erratic markup
link_matcher = re.compile('((?:%s)="%s[^<>"]*")' % ("|".join(url_attributes), re.escape(settings.MEDIA_URL)))

def append_modtime_to_url(url):
    """Append the file modification time to URL if the URL is in
    MEDIA_URL and corresponds to a file in MEDIA_ROOT."""
    if not url.startswith(settings.MEDIA_URL):
        return url
    filename = os.path.join(settings.MEDIA_ROOT, url[len(settings.MEDIA_URL):])
    index = filename.rfind('?')
    contains_question_mark = index != -1
    
    if contains_question_mark:
        filename = filename[:index]
        
    try:
        stat = os.stat(filename)
        timestamp = str(int(stat.st_mtime))
        return url + ('&_=' if contains_question_mark else '?_=') + timestamp 
    except OSError:
        pass

    return url

def append_modtime_to_urls_in_html(html):
    """Add modification time GET parameter to each media URL in input."""
    def replace_urls(m):
        before, url, after = m.group(1).split('"')

        return before + '"' + append_modtime_to_url(url) + '"' + after

    return link_matcher.sub(replace_urls, html)

class ModTimeUrlsMiddleware:
    """Middleware for adding modtime GET parameter to each media URL in responses."""
    
    def process_response(self, request, response):
        if 'text/html' in response['content-type'].lower():
            response.content = append_modtime_to_urls_in_html(response.content)
        return response
