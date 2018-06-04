from django.urls import path, re_path
from django.conf import settings
import django.views.static

import oisfixes.views

urlpatterns = [
    re_path(r'^(?:media|static)/(.*)$', django.views.static.serve, {'document_root': settings.STATIC_ROOT }),
    path('robots.txt', oisfixes.views.robots_txt, {'template': 'robots.txt', 'mimetype': 'text/plain'}),

    path('', oisfixes.views.intro, name="intro_page"),
    path('vejnavn/', oisfixes.views.correct_way, name="correct_way"),
    path('rettelser/', oisfixes.views.corrections, name="corrections_overview"),
    path('rettelser/<int:correction_id>/slet/', oisfixes.views.delete_correction, name="delete_correction"),
    path('rettelser/<int:correction_id>/', oisfixes.views.correction_details, name="correction_details"),

    path('api/searchaddressnodes/', oisfixes.views.search_for_address_nodes, name="search_for_address_nodes"),
    path('api/createwaycorrection/', oisfixes.views.create_way_correction, name="create_way_correction"),
    path('api/getwaycorrections/', oisfixes.views.get_way_corrections, name="get_way_corrections"),
]
