from xml.etree import ElementTree

def extract_address_node_results(xml, ways):
    # extract some info from address nodes and put them into ways
    # based on which way they belong to
    
    # unfortunately, we have to deal with multiple keys
    municipality_no_keys = ["kms:municipality_no", "osak:municipality_no"]
    street_no_keys = ["kms:street_no", "osak:street_no"]
    postcode_keys = ["addr:postcode"]
    city_keys = ["addr:city"]

    def extract_value_from_keys(node, keys):
        val = None
        for k in keys:
            for n in node:
                if n.attrib.get("k") == k and "v" in n.attrib:
                    val = n.attrib["v"]
                
        return val

    # go through the nodes
    nodes = ElementTree.fromstring(xml).findall("node")
    for n in nodes:
        municipality_no = extract_value_from_keys(n, municipality_no_keys)
        street_no = extract_value_from_keys(n, street_no_keys)

        if municipality_no == None or street_no == None:
            continue
        
        way_key = (municipality_no, street_no)
        if way_key in ways:
            continue
        
        ways[way_key] = dict(
            municipality_no=municipality_no,
            street_no=street_no,
            node_id=n.get("id"),
            node_lat=n.get("lat"),
            node_lon=n.get("lon"),
            node_postcode=extract_value_from_keys(n, postcode_keys),
            node_city=extract_value_from_keys(n, city_keys)
            )

# requires python-oauth2, from the example in the documentation
# at https://github.com/dgouldin/python-oauth2
import oauth2 as oauth
import urlparse
from django.utils.http import urlquote
from django.http import HttpResponseRedirect
from django.conf import settings

consumer = oauth.Consumer(settings.OSM_OAUTH_KEY, settings.OSM_OAUTH_SECRET)
client = oauth.Client(consumer)

class OAuthException(Exception): pass

def do_oauth_authentication(request):
    # Step 1. Get a request token from Twitter.
    resp, content = client.request(settings.OSM_BASE_URL + "oauth/request_token", "GET")
    if resp['status'] != '200':
        raise Exception("Invalid OAuth response.")

    # Step 2. Store the request token in a session for later use.
    request.session['oauth_request_token'] = dict(urlparse.parse_qsl(content))

    # Step 3. Redirect the user to the authentication URL.
    url = "%s?oauth_token=%s&oauth_callback=%s" % (
        settings.OSM_BASE_URL + "oauth/authorize",
        request.session['oauth_request_token']['oauth_token'],
        urlquote(request.build_absolute_uri(request.get_full_path() + "?oauth_authenticated=1"))
        )

    return HttpResponseRedirect(url)


def oauth_authenticated(request):
    # Step 1. Use the request token in the session to build a new client.
    request_token = request.session['oauth_request_token']
    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    # Step 2. Request the authorized access token from the service.
    resp, content = client.request(settings.OSM_BASE_URL + "oauth/access_token", "GET")
    if resp['status'] != '200':
        raise OAuthException("Invalid OAuth response.")

    del request.session['oauth_request_token']
    request.session['oauth_access_token'] = dict(urlparse.parse_qsl(content))


def oauth_authentication_required(f):
    def inner(request, *args, **kwargs):
        if "oauth_access_token" in request.session:
            return f(request, *args, **kwargs)

        if "oauth_request_token" in request.session:
            if "oauth_authenticated" in request.GET:
                oauth_authenticated(request)

                return HttpResponseRedirect(request.path)

        return do_oauth_authentication(request)

        try:
            pass
        except OAuthException, e:
            return HttpResponse("OAuth failed") # FIXME: do something

    return inner


def fill_in_osm_user(request):
    # request user details
    access_token = request.session['oauth_access_token']
    token = oauth.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)
    resp, content = client.request(settings.OSM_BASE_URL + "api/0.6/user/details", "GET")

    if resp['status'] != '200':
        raise OAuthException("Invalid user details response %s." % resp['status'])

    user = ElementTree.fromstring(content).find("user")
    try:
        user_id = int(user.attrib["id"])
        user_name = user.attrib["display_name"]
    except:
        raise OAuthException("Couldn't parse user response.")

    # save user details in database
    from main.models import OsmUser

    try:
        user = OsmUser.objects.get(id=user_id)
    except OsmUser.DoesNotExist:
        user = OsmUser(id=user_id)

    if user.name != user_name:
        user.name = user_name
        user.save()

    # and save it in session
    request.session["osm_user"] = user_id

def osm_user_required(f):
    def inner(request, *args, **kwargs):
        if "osm_user" not in request.session:
            if "oauth_access_token" not in request.session:
                return oauth_authentication_required(f)(request, *args, **kwargs)
            else:
                fill_in_osm_user(request)

        return f(request, *args, **kwargs)
    
    return inner
        
    
    
