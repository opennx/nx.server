#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import route, run, template, static_file

MENU_ITEMS = [("index","Home"),("installs","Installs"),("porn","Porn")]

@route('/')
@route('/<name>')
def index(name='index'):
    return template('main', menu_items=MENU_ITEMS,current_page=name)


@route('/static/<path:path>')
def callback(path):
    return static_file(path, root=os.path.join(os.getcwd(),'static'))


if __name__ == "__main__":
    print os.path.join(os.getcwd(),'static')
    