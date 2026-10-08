"""Test-only HTTP and admin entry points."""

from dict_field.views import edit_order
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("orders/new/", edit_order, name="order-create"),
    path("orders/<int:pk>/", edit_order, name="order-edit"),
    path("admin/", admin.site.urls),
]
