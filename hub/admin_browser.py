from nx import *

def admin_browser(context, *args, **kwargs):
    context["title"] = "browser neasi"
    context["columns"] = "title", "duration", "genre", "id_folder"
    context["assets"] = list(browse(genre="Horror"))
    return context
