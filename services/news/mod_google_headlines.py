#!/usr/bin/env python 

import urllib2
import re
import sys

from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup as BS
from xml.etree import ElementTree as ET


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
    

def get_data(rss_url):
    feed = urllib2.urlopen(rss_url).read()
    
    try:    
        xfeed = ET.XML(feed).find("channel")
    except: 
        return
     
    for item in xfeed.findall("item"):
        guid       = item.find("guid").text.strip()
        title_elms = item.find("title").text.strip().split("-")
        title =  " ".join(title_elms[:-1]).strip()
        source = title_elms[-1].strip()
        
        if title.endswith("..."):
            continue
          
        desc1 = item.find("description").text.strip() 
      
        matcher = r".*</font></b></font><br /><font size=\"-1\">(?P<article>.*?)\</font>.*"
        m = re.match(matcher, desc1)
        if not m:
            continue

        desc2 = m.group("article")
        
        if desc2.endswith("<b>...</b>"): 
            desc2 = ". ".join(desc2.split(". ")[:-1]).strip()+"."
         
        article = {}
        article["title"] = title
        article["source"] = source
        article["identifier/guid"]    = guid

        article["content_type"] = 0 #text
        article["media_type"] = 1 # virutal

        article["article"] = re.sub(r"(\| foto (.*))\.",".",strip_tags(desc2)).replace("|"," ")
        if article["article"].endswith("..."):
            continue
        if len(article["article"]) < 10:
            continue

        yield article




def google_headlines(config=False):
    if not config:
        config = {
        "google_domov": "https://news.google.com/news/feeds?pz=1&cf=all&ned=cs_cz&hl=cs&topic=n&output=rss",
        "google_svet":  "https://news.google.com/news/feeds?pz=1&cf=all&ned=cs_cz&hl=cs&topic=w&output=rss" 
        }
    guids = []
    for group in config:
        for article in get_data(config[group]):
            if article["identifier/guid"] in guids:
                continue
            guids.append(article["identifier/guid"])
            article["news_group"] = group
            yield article


if __name__ == "__main__":
    for i in google_headlines():
        print i[2]["title"]
