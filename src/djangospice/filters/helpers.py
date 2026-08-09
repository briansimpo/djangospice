from django.db.models import Q, QuerySet, Model # type: ignore


def dynamic_filter(model: Model, filters, **kwargs) -> QuerySet:

    # Step 1: Base queryset
    if isinstance(filters, Q):
        queryset = model.objects.filter(filters)
    elif isinstance(filters, dict):
        queryset = model.objects.filter(**filters)
    elif isinstance(filters, QuerySet):
        queryset = filters
    else:
        raise ValueError("Expected 'filters' to be a Q object, dict, or QuerySet.")

    # Step 2: Get nullable fields
    nullable_fields = {
        field.name for field in model._meta.get_fields()
        if hasattr(field, 'null') and field.null
    }

    # Step 3: Apply optional filters
    for key, value in kwargs.items():
        if value in [None, "", []]:
            continue  # skip empty values

        # Extract base field name (before any lookups)
        base_field = key.split("__")[0]

        # More precise: apply only if this value exists in non-null rows
        if base_field in nullable_fields:
            if queryset.filter(**{key: value}).exclude(**{base_field: None}).exists():
                queryset = queryset.filter(**{key: value})
        else:
            queryset = queryset.filter(**{key: value})

    return queryset


def dynamic_queryset(queryset:QuerySet, filters, **kwargs) -> QuerySet:
   
    # Step 1: Base queryset
    if isinstance(filters, Q):
        queryset = queryset.filter(filters)
    elif isinstance(filters, dict):
        queryset = queryset.filter(**filters)
    elif isinstance(filters, QuerySet):
        queryset = filters
    else:
        raise ValueError("Expected 'filters' to be a Q object, dict, or QuerySet.")

    # Step 2: Get nullable fields
    nullable_fields = {
        field.name for field in queryset.model._meta.get_fields()
        if hasattr(field, 'null') and field.null
    }

    # Step 3: Apply optional filters
    for key, value in kwargs.items():
        if value in [None, "", []]:
            continue  # skip empty values

        # Extract base field name (before any lookups)
        base_field = key.split("__")[0]

        # More precise: apply only if this value exists in non-null rows
        if base_field in nullable_fields:
            if queryset.filter(**{key: value}).exclude(**{base_field: None}).exists():
                queryset = queryset.filter(**{key: value})
        else:
            queryset = queryset.filter(**{key: value})

    return queryset

