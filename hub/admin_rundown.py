from nx import *

def admin_rundown(context, *args, **kwargs):
    context["title"] = "tohle je nazev rundownu"
    return context
