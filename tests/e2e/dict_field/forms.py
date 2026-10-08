"""Application forms used through ORM, HTTP, and admin workflows."""

from django import forms

from dict_field.models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("customer", "status", "snapshot")
