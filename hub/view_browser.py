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

        records_per_page = 1000
        columns = ["id", "title", "genre", "duration"]

        assets = api_get(
               fulltext=kwargs.get("fulltext"),
               count=True,
               limit=records_per_page
            )

        self["page_count"] = int(math.ceil(assets["count"] / records_per_page))
        self["current_page"] = 1
        self["columns"] = columns
        self["data"] = [Asset(meta=meta) for meta in assets["data"]]

