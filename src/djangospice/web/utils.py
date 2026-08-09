def is_htmx(request):
    if request.headers.get("HX-Request"):
        return True
    else:
        return False
    
    
def is_ajax(request):
    """
    Returns True if the request is an AJAX request.
    """
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def is_json(request):
    if request.accepts("application/json"):
        return True
    else:
        return False