
def get_instance(model_class, instance):
    if instance:
        if not isinstance(instance, model_class):
            # If instance is not of model_class type, assume it's a primary key and fetch the object
            return model_class.objects.get(pk=instance)
        return instance  # Return the object if it's already an instance of model_class
    return None  # Return None if the instance is None

