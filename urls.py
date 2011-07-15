from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
                       
    (r'^$', 'main.views.intro'),
    (r'^vejnavn/$', 'main.views.correct_way'),
    (r'^rettelser/$', 'main.views.corrections'),
    (r'^rettelser/(?P<correction_id>[0-9]+)/slet/$', 'main.views.delete_correction'),
    (r'^rettelser/(?P<correction_id>[0-9]+)/$', 'main.views.correction_details'),

    (r'^api/searchaddressnodes/$', 'main.views.search_for_address_nodes'),
    (r'^api/createwaycorrection/$', 'main.views.create_way_correction'),
    (r'^api/getwaycorrections/$', 'main.views.get_way_corrections'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),
)
