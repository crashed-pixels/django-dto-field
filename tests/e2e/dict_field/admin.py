"""Register a DTO-bearing model for real admin add/change requests."""

from django.contrib import admin

from dict_field.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    fields = ("customer", "status", "snapshot")
