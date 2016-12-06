from cherryadmin import CherryAdmin

from nebula import *

from .view_browser import ViewBrowser
from .view_dashboard import ViewDashboard

__all__ = [
        "CherryAdmin",
        "hub_config",
    ]

def login_helper(login, password):
    user = get_user(login, password)
    if not user:
        return False
    return user.meta

def site_context_helper():
    context = config
    context["name"] = config["site_name"]
    context["meta_types"] = meta_types
    context["js"] = [
            "/static/js/vendor.min.js",
            "/static/js/main.js"
        ]
    context["css"] = [
            "//fonts.googleapis.com/css?family=Roboto:300,400,500,700&subset=latin-ext",
            "//fonts.googleapis.com/css?family=Roboto+Slab&subset=latin-ext",
            "//fonts.googleapis.com/icon?family=Material+Icons",
            "/static/css/main.css"
        ]
    return context


def page_context_helper():
    return {}


hub_config = {
        "static_dir" : "hub/static",
        "templates_dir" : "hub/templates",
        "login_helper" : login_helper,
        "site_context_helper" : site_context_helper,
        "page_context_helper" : page_context_helper,
        "blocking" : True,
        "views" : {
                "index" : ViewDashboard,
                "browser" : ViewBrowser
            },
        "api_methods" : {
                "get" : api_get,
                "rundown" : api_rundown,
                "settings" : api_settings,
                "meta_types" : api_meta_types,
            }
    }
