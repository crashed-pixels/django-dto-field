"""Minimal create/edit views exercising real Django request handling."""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from dict_field.forms import OrderForm
from dict_field.models import Order


def edit_order(request, pk=None):
    instance = get_object_or_404(Order, pk=pk) if pk is not None else None
    form = OrderForm(
        request.POST if request.method == "POST" else None, instance=instance
    )
    if request.method == "POST" and form.is_valid():
        order = form.save()
        return redirect("order-edit", pk=order.pk)
    status = 400 if request.method == "POST" else 200
    return HttpResponse(form.as_p(), status=status)
