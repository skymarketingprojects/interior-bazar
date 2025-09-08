from django.db import models
def shiftUp(model_class: models.Model, start_index: int, exclude_pk=None):
    """
    Increments the index of all instances from `start_index` onward.
    """
    objects = model_class.objects.filter(index__gte=start_index)
    if exclude_pk:
        objects = objects.exclude(pk=exclude_pk)
    objects = list(objects.order_by("-index"))

    for obj in objects:
        obj.index += 1

    model_class.objects.bulk_update(objects, ["index"])


def shiftDown(model_class: models.Model, start_index: int, end_index: int, exclude_pk=None):
    """
    Decrements the index of all instances between start_index and end_index.
    """
    objects = model_class.objects.filter(index__gte=start_index, index__lt=end_index+1)
    if exclude_pk:
        objects = objects.exclude(pk=exclude_pk)
    objects = list(objects.order_by("index"))

    for obj in objects:
        obj.index -= 1

    model_class.objects.bulk_update(objects, ["index"])


def shiftUpRange(model_class: models.Model, start_index: int, end_index: int, exclude_pk=None):
    """
    Increments the index of all instances between start_index and end_index.
    """
    objects = model_class.objects.filter(index__gt=start_index-1, index__lte=end_index)
    if exclude_pk:
        objects = objects.exclude(pk=exclude_pk)
    objects = list(objects.order_by("-index"))

    for obj in objects:
        obj.index += 1

    model_class.objects.bulk_update(objects, ["index"])

def indexShifting(instance: models.Model):
    model_class = instance.__class__

    if instance.pk:
        old_index = model_class.objects.get(pk=instance.pk).index

        if old_index < instance.index:
            shiftDown(model_class, old_index, instance.index, exclude_pk=instance.pk)
        elif old_index > instance.index:
            shiftUpRange(model_class, instance.index, old_index, exclude_pk=instance.pk)

    else:
        if model_class.objects.filter(index=instance.index).exists():
            shiftUp(model_class, instance.index)