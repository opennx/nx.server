import math

from nebula import *
from cherryadmin import CherryAdminView

class ViewBrowser(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "browser"
        self["title"] = "Browser"
        self["js"] = [
                "/static/js/browser.js"
            ]

        records_per_page = 200

        # args

        try:
            id_view = int(kwargs.get("v"))
            if not id_view in config["views"].keys():
                raise KeyError
        except (KeyError, ValueError, TypeError):
            id_view = min(config["views"].keys())

        try:
            current_page = int(kwargs["p"])
        except (KeyError, ValueError, TypeError):
            current_page = 1

        search_query = kwargs.get("q", "")

        # View settings

        view_config = config["views"][id_view]
        columns = view_config["columns"]

        conds = []

        if "folders" in view_config:
            conds.append("id_folder IN ({})".format(view_config["folders"]))
        if "media_types" in view_config:
            conds.append("media_type IN ({})".format(view_config["media_types"]))
        if "content_types" in view_config:
            conds.append("content_type IN ({})".format(view_config["content_types"]))
        if "origins" in view_config:
            conds.append("origin IN ({})".format(view_config["origins"]))
        if "statuses" in view_config:
            conds.append("status IN ({})".format(view_config["statuses"]))
        if "query" in view_config:
            conds.append("id_object in ({})".format(view_config["query"]))

        #
        # get data
        #

        assets = api_get(
                conds=conds,
                fulltext=search_query or False,
                count=True,
                limit=records_per_page,
                offset=(current_page - 1)*records_per_page
            )

        #
        # page context
        #

        # helper for pagination
        fargs = []
        if id_view != 1:
            fargs.append("v="+str(id_view))
        if search_query:
            fargs.append("q="+search_query)
        self["filter_args"] = "?" + "&amp;".join(fargs) if fargs else ""


        # the rest
        self["id_view"] = id_view
        self["search_query"] = search_query
        self["current_page"] = current_page

        self["page_count"] = int(math.ceil(assets["count"] / records_per_page))
        self["columns"] = columns
        self["data"] = [Asset(meta=meta) for meta in assets["data"]]

