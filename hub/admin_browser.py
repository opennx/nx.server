from nx import *

def admin_browser(context, *args, **kwargs):
    context["title"] = "browser neasi"
    context["columns"] = "title", "duration", "genre", "id_folder"
    context["assets"] = [asset for asset in api_get(fulltext="rock")]
    return context
