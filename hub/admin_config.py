from nx import *

def admin_config(context, *args, **kwargs):
    context["title"] = "nebula configuration"
    return context
