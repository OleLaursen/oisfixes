# -*- coding: utf-8 -*-

import urllib.request, urllib.error, urllib.parse, socket
import datetime

from django.template.loader import render_to_string
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.utils.encoding import iri_to_uri
from django.urls import reverse as urlreverse
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django import forms

from osm.helpers import osm_user_required, extract_address_node_results
from osm.models import OsmUser
from oisfixes.helpers import Page, render_page
from oisfixes.models import WayCorrection

def robots_txt(request):
    return render(request, "robots.txt", {}, content_type="text/plain")

def intro(request):
    request.page = Page()
    request.page.title = "OIS-rettelser til OpenStreetMap"
    request.page.css.append("intro.css")
    request.page.content = render_to_string("intro.html",
                                            request=request)
    
    return render_page(request)

@osm_user_required
def correct_way(request):
    request.page = Page()
    request.page.title = "Rapportér rettelse til OIS-vejnavn"
    request.page.js.append("correct-way.js")
    request.page.css.append("correct-way.css")

    name = request.GET.get("navn", "")
    municipality_no = request.GET.get("kmn")
    street_no = request.GET.get("vej")
    
    try:
        municipality_no = int(municipality_no)
        street_no = int(street_no)
    except (ValueError, TypeError):
        municipality_no = "null"
        street_no = "null"
        
    request.page.content = render_to_string(
        "correct-way.html", {
            "name": name,
            "municipality_no": municipality_no,
            "street_no": street_no
        }, request=request)

    return render_page(request)

@osm_user_required
def delete_correction(request, correction_id):
    correction = get_object_or_404(WayCorrection, id=correction_id)
    
    request.page = Page()
    request.page.title = "Slet rettelse %s" % correction.id

    msg = ""

    if request.method == "POST":
        comment = request.POST.get("comment")
        if comment:
            correction.deleted = datetime.datetime.now()
            correction.deleted_by_id = request.session["osm_user"]
            correction.deleted_comment = comment
            correction.save()

            return HttpResponseRedirect(urlreverse("correction_details", kwargs=dict(correction_id=correction.id)))
        else:
            msg = "Du skal skrive en forklaring."
    
    request.page.content = render_to_string(
        "delete-correction.html", {
            "c": correction,
            "msg": msg
        }, request=request)

    return render_page(request)

    
def search_for_address_nodes(request):
    ways = {}

    name = request.GET.get("name", "").strip()
    name = name.replace("]", "")

    if name:
        # ask OpenStreetMap XAPI for address nodes
        
        #xapi_base_url = "https://open.mapquestapi.com/xapi/api/0.6/"
        xapi_base_url = "https://www.overpass-api.de/api/xapi?"

        ois_street_keys = ["addr:street", "osak:street"]
        
        for k in ois_street_keys:
            query = iri_to_uri("node[%s=%s]" % (urllib.parse.quote(k), urllib.parse.quote(name)))
            url = xapi_base_url + query
            try:
                url_response = urllib.request.urlopen(url, timeout=60)
                xml = url_response.read()
            except (urllib.error.URLError, socket.timeout, socket.error) as e:
                if hasattr(e, "reason"):
                    reason = e.reason
                else:
                    reason = str(e)
                msg = 'Fejl ved søgning på OpenStreetMap XAPI (%s). Dette skyldes typisk at en OpenStreetMap-server er overbelastet i øjeblikket, du kan prøve igen senere. Du kan også prøve at gå til <a href="%s">den forsøgte søgning</a> for at se hvad fejlen helt nøjagtigt er.' % (reason, url)
                return JsonResponse({
                    "error": msg
                })
            
            extract_address_node_results(xml, ways)
            
        #extract_address_node_results(open("tmp.xml").read(), ways)

    results = list(ways.values())
    results.sort(key=lambda x: (x["municipality_no"], x["street_no"]))

    # add existing corrections
    way_filter = Q()
    for x in results:
        way_filter |= Q(municipality_no=x["municipality_no"], street_no=x["street_no"])
    corrections = dict(((c.municipality_no, c.street_no), c)
                       for c in WayCorrection.objects.filter(way_filter, deleted=None))

    for x in results:
        c = corrections.get((x["municipality_no"], x["street_no"]))
        if c:
            x["correction"] = "%s &rarr; %s" % (c.old_name, c.new_name)
        else:
            x["correction"] = ""
            
    
    return JsonResponse({
        "name": name,
        "results": results,
    })


class WayCorrectionForm(forms.ModelForm):
    class Meta:
        fields = ("municipality_no", "street_no", "old_name", "new_name", "node_id", "lat", "lon", "comment")
        model = WayCorrection
        

def create_way_correction(request):
    if "osm_user" not in request.session:
        return HttpResponseForbidden("Must be authorized via OpenStreetMap OAuth.")

    form = WayCorrectionForm(request.POST)
    if form.is_valid():
        correction = form.save(commit=False)
        correction.created_by_id = request.session["osm_user"]
        correction.save()
        
        old_corrections = WayCorrection.objects.filter(
            municipality_no=correction.municipality_no,
            street_no=correction.street_no,
            old_name=correction.old_name,
            deleted=None,
            ).exclude(id=correction.id)
        
        for o in old_corrections:
            o.deleted = correction.created
            o.deleted_by = correction.created_by
            o.deleted_comment = "Erstattet af %s" % correction.id
            o.deleted_replaced_by = correction
            o.save()

        replaced = ""
        if old_corrections:
            replaced = " (erstattede %s %s)" % (
                len(old_corrections),
                "rettelse" if len(old_corrections) == 1 else "rettelser")

        report_url = urlreverse("correction_details", kwargs=dict(correction_id=correction.id))
        result = 'Oprettede <a href="%s">ny rettelse</a>%s. Du kan <a href="http://osm.ter.dk/address_street.php?MunicipalityCode=%s&StreetCode=%s">genimportere adressepunkterne med importeringsscriptet</a>.' % (report_url, replaced, correction.municipality_no, correction.street_no)
    else:
        result = "Fejl ved fortolkning af indsendte data."
    
    return JsonResponse({
        "result": result,
    })


def corrections(request):
    request.page = Page()
    request.page.title = "OIS-rettelser til OpenStreetMap"
    request.page.css.append("corrections.css")

    corrections = WayCorrection.objects.all().order_by("-created").select_related("created_by", "deleted_by")

    deleted = request.GET.get("slettet")
    if deleted:
        corrections = corrections.exclude(deleted=None)
    else:
        corrections = corrections.filter(deleted=None)

    user = request.GET.get("bruger")
    if user:
        user = get_object_or_404(OsmUser, id=user)
        corrections = corrections.filter(Q(created_by=user) | Q(deleted_by=user))

    request.page.content = render_to_string(
        "corrections.html", {
            "corrections": corrections,
            "show_deleted": deleted,
            "show_user": user
        }, request=request)
        
    return render_page(request)

def correction_details(request, correction_id):
    correction = get_object_or_404(WayCorrection, id=correction_id)
    
    request.page = Page()
    request.page.js.append("https://www.openlayers.org/api/OpenLayers.js")
    request.page.js.append("map.js")
    request.page.css.append("correction-details.css")
    request.page.title = "OIS-rettelse %s" % correction.id
    request.page.content = render_to_string(
        "correction-details.html", {
        "c": correction
        }, request=request)

    return render_page(request)

def get_way_corrections(request):
    corrections = WayCorrection.objects.filter(deleted=None).order_by("-created").select_related("created_by")

    municipality_no = request.GET.get("municipality_no")
    if municipality_no:
        corrections = corrections.filter(municipality_no=municipality_no)
    
    street_no = request.GET.get("street_no")
    if street_no:
        corrections = corrections.filter(street_no=street_no)

    columns = dict(osak_street=0,
                   addr_street=1,
                   municipality_no=2,
                   street_no=3,
                   id=4,
                   comment=5,
                   created=6,
                   created_by=7,
                   )

    data = [(x.old_name, x.new_name, x.municipality_no, x.street_no,
             x.id, x.comment, x.created.strftime("%Y-%m-%dT%H:%M:%S"),
             x.created_by.name) for x in corrections]
    
    return JsonResponse({
        "columns": columns,
        "data": data,
    })
    
