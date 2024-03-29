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

# requires python3-oauth2client, from the example in the documentation
# at https://github.com/dgouldin/python-oauth2
import oauth2 as oauth
import urllib.parse
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

consumer = oauth.Consumer(settings.OSM_OAUTH_KEY, settings.OSM_OAUTH_SECRET)

class OAuthException(Exception): pass

def do_oauth_authentication(request):
    # Step 1. Get a request token.
    client = oauth.Client(consumer)
    url = settings.OSM_BASE_URL + "oauth/request_token"
    try:
        resp, content = client.request(url, "GET")
    except Exception as e:
        raise OAuthException("Error sending request to OpenStreetMap server on %s (%s)" % (url, e))

    if resp['status'] != '200':
        raise OAuthException("OpenStreetMap server returned status code %s instead of 200 OK on %s" % (resp['status'], url))

    # Step 2. Store the request token in a session for later use.
    content = content.decode()
    request.session['oauth_request_token'] = dict(urllib.parse.parse_qsl(content))

    # Step 3. Redirect the user to the authentication URL.
    url = "%s?oauth_token=%s&oauth_callback=%s" % (
        settings.OSM_BASE_URL + "oauth/authorize",
        request.session['oauth_request_token']['oauth_token'],
        urllib.parse.quote(request.build_absolute_uri(request.get_full_path() + "?oauth_authenticated=1"))
        )

    return HttpResponseRedirect(url)


def oauth_authenticated(request):
    # Step 1. Use the request token in the session to build a new client.
    request_token = request.session['oauth_request_token']
    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    # Step 2. Request the authorized access token from the service.
    url = settings.OSM_BASE_URL + "oauth/access_token"
    resp, content = client.request(url, "GET")
    if resp['status'] != '200':
        raise OAuthException("OpenStreetMap server returned status code %s instead of 200 OK on %s" % (resp['status'], url))

    content = content.decode()
    del request.session['oauth_request_token']
    request.session['oauth_access_token'] = dict(urllib.parse.parse_qsl(content))


def oauth_authentication_required(f):
    def inner(request, *args, **kwargs):
        if "oauth_access_token" in request.session:
            return f(request, *args, **kwargs)

        if "oauth_request_token" in request.session:
            if "oauth_authenticated" in request.GET:
                oauth_authenticated(request)

                return HttpResponseRedirect(request.path)
        try:
            return do_oauth_authentication(request)
        except OAuthException as e:
            return HttpResponse("Communication with OpenStreetmap server failed (%s)" % e)

    return inner


def fill_in_osm_user(request):
    # request user details
    access_token = request.session['oauth_access_token']
    token = oauth.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)
    resp, content = client.request(settings.OSM_BASE_URL + "api/0.6/user/details", "GET")

    if resp['status'] != '200':
        raise OAuthException("Invalid user details response %s." % resp['status'])

    content = content.decode()

    user = ElementTree.fromstring(content).find("user")
    try:
        user_id = int(user.attrib["id"])
        user_name = user.attrib["display_name"]
    except:
        raise OAuthException("Couldn't parse user response.")

    # save user details in database
    from oisfixes.models import OsmUser

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
        
    
    
