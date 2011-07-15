import datetime

from django.db import models
from osm.models import OsmUser

class WayCorrection(models.Model):
    old_name = models.CharField(max_length=255)
    new_name = models.CharField(max_length=255)
    municipality_no = models.CharField(max_length=10)
    street_no = models.CharField(max_length=10)
    node_id = models.CharField(max_length=20)
    lat = models.CharField(max_length=20)
    lon = models.CharField(max_length=20)
    comment = models.CharField(max_length=255)

    created = models.DateTimeField(default=datetime.datetime.now)
    created_by = models.ForeignKey(OsmUser)

    deleted = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(OsmUser, related_name="deletedwaycorrection_set", blank=True, null=True)
    deleted_comment = models.CharField(max_length=255, blank=True)
    deleted_replaced_by = models.ForeignKey('WayCorrection', blank=True, null=True)

    def __unicode__(self):
        return u"%s %s -> %s" % (self.id, self.old_name, self.new_name)
