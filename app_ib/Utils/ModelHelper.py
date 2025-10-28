from django.db import models
from typing import Optional
from app_ib.Utils.MyMethods import MY_METHODS
def shiftUp(model_class: models.Model, start_index: int, filter_attr: Optional[str] = None, filter_value=None, exclude_pk=None):
    objects = model_class.objects.filter(index__gte=start_index)
    if filter_attr and filter_value is not None:
        objects = objects.filter(**{filter_attr: filter_value})
    if exclude_pk:
        objects = objects.exclude(pk=exclude_pk)
    objects = list(objects.order_by("-index"))

    for obj in objects:
        obj.index += 1

    if objects:
        model_class.objects.bulk_update(objects, ["index"])


def shiftDown(model_class: models.Model, start_index: int, end_index: int, filter_attr: Optional[str] = None, filter_value=None, exclude_pk=None):
    objects = model_class.objects.filter(index__gte=start_index, index__lte=end_index)
    if filter_attr and filter_value is not None:
        objects = objects.filter(**{filter_attr: filter_value})
    if exclude_pk:
        objects = objects.exclude(pk=exclude_pk)
    objects = list(objects.order_by("index"))

    for obj in objects:
        obj.index -= 1

    if objects:
        model_class.objects.bulk_update(objects, ["index"])


def shiftUpRange(model_class: models.Model, start_index: int, end_index: int, filter_attr: Optional[str] = None, filter_value=None, exclude_pk=None)->None:
    objects = model_class.objects.filter(index__gte=start_index, index__lte=end_index)
    if filter_attr and filter_value is not None:
        objects = objects.filter(**{filter_attr: filter_value})
    if exclude_pk:
        objects = objects.exclude(pk=exclude_pk)
    objects = list(objects.order_by("-index"))

    for obj in objects:
        obj.index += 1

    if objects:
        model_class.objects.bulk_update(objects, ["index"])


def indexShifting(instance: models.Model, filter_attr: Optional[str] = None):
    """
    Shifts indexes for an instance, optionally filtered by a single attribute.
    If filter_attr is None, all instances are considered.
    """
    model_class = instance.__class__
    filter_value = getattr(instance, filter_attr) if filter_attr else None

    if instance.pk:
        old_index = model_class.objects.get(pk=instance.pk).index

        if old_index < instance.index:
            shiftDown(model_class, old_index, instance.index, filter_attr=filter_attr, filter_value=filter_value, exclude_pk=instance.pk)
        elif old_index > instance.index:
            shiftUpRange(model_class, instance.index, old_index, filter_attr=filter_attr, filter_value=filter_value, exclude_pk=instance.pk)

    else:
        if model_class.objects.filter(index=instance.index, **({filter_attr: filter_value} if filter_attr else {})).exists():
            shiftUp(model_class, instance.index, filter_attr=filter_attr, filter_value=filter_value)

def applyDiscount(instance: models.Model)->float:
    """
    Safely calculates display price based on discount type and discount amount.
    If discountType == 'percent', applies a percentage discount.
    If discountType == 'amount', subtracts the amount directly.
    If anything goes wrong, displayPrice = orignalPrice.
    Ensures displayPrice is never below 0.
    """
    try:
        original_price = float(instance.orignalPrice)
        discount_type = str(instance.discountType or '').lower().strip()
        discount_by = float(instance.discountBy or 0)

        print(f"Calculating discount for original_price: {original_price}, discount_type: {discount_type}, discount_by: {discount_by}")
        if discount_type == 'percent':
            discount_amount = (discount_by / 100) * original_price
        else:
            discount_amount = discount_by

        calculated_price = original_price - discount_amount
        print(f"Calculated display price: {calculated_price}")
        # Ensure price never drops below zero
        return max(calculated_price, 0)

    except Exception as e:
        print(f"Error in applyDiscount: {str(e)}")
        # If any error occurs (missing or invalid values), fall back to original price
        return max(float(getattr(instance, 'orignalPrice', 0) or 0), 0)