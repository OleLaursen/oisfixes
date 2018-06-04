from django.contrib import admin

from .models import *

class WayCorrectionAdmin(admin.ModelAdmin):
    list_display = ("id", "municipality_no", "street_no", "old_name", "new_name", "created", "created_by", "deleted", "deleted_by")
    search_fields = ("old_name", "created_by__name",)
    ordering = ("-created",)
    raw_id_fields = ("deleted_replaced_by",)

admin.site.register(WayCorrection, WayCorrectionAdmin)
