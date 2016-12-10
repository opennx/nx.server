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
        for key, col in [
                    ["folders", "id_folder"],
                    ["media_types", "media_type"],
                    ["content_types", "content_type"],
                    ["origins", "origin"],
                    ["statuses", "status"],
                    ["folders", "id_folder"],
                ]:
            if key in view_config:
                if len(view_config[key].split(",")) == 1:
                    conds.append("{}={}".format(col, view_config[key]))
                else:
                    conds.append("{} IN ({})".format(col, view_config[key]))

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

