#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import jinja2

reload(sys)
sys.setdefaultencoding('utf-8')

import thread
import hashlib

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from auth import *

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)


SECRET_KEY = "yeah, not actually a secret"
DEBUG = True
 

app = Flask(__name__, )
app.config.from_object(__name__)

login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"
login_manager.setup_app(app)



@login_manager.user_loader
def load_user(id):
    return FlaskUser(int(id))


########################################################################
## APP TEMPLATE FILTERS

@app.template_filter('datetime')
def _jinja2_filter_datetime(date, format='%Y-%m-%d %H:%M:%S'):
    return str(time.strftime(format, time.localtime(date)))

@app.template_filter('date')
def _jinja2_filter_datetime(date, format='%Y-%m-%d'):
    return str(time.strftime(format, time.localtime(date)))


########################################################################
## APP ROUTES

@app.route("/")
def index():
    current_controller = set_current_controller({'title': 'Dashboard', 'controller': 'dashboard' })
    return render_template("index.html", current_controller=current_controller)


@app.route("/browser")
def browser():
    assets = view_browser()
    current_controller = set_current_controller({'title': 'Browser', 'controller': 'browser' })
    return render_template("browser.html", assets=assets, current_controller=current_controller)


 
@app.route("/jobs", methods=['GET', 'POST'])
@app.route("/jobs/<view>", methods=['GET', 'POST'])
@app.route("/jobs/<view>/search", methods=['GET'])
@app.route("/jobs/<view>/search/<search>", methods=['GET'])
def jobs(view="active", search=""):

    if request.method == "POST" and "id_job" and "action" in request.form:
        id_job = int(request.form.get("id_job"))
        action = int(request.form.get("action"))
        action_result = job_action(id_job, action, id_user=current_user.id)
        flash("Job {} restarted".format(id_job), "info")
        return json.dumps(action_result)

        
    if view == "failed":
        current_view = "failed"
    elif view == "completed":
        current_view = "completed"
    elif view == "json":
        current_view = "json"
    else:
        current_view = "active" 

    jobs = view_jobs(current_view, search)
    if view=="json":
        return jobs

    current_controller = set_current_controller({'title': 'Jobs', 'current_view': current_view, 'controller': 'jobs', 'search': search })   
    return render_template("job_monitor.html", jobs=jobs, current_controller=current_controller)




@app.route("/services",methods=['GET', 'POST'])
@app.route("/services/<view>")
def services(view="default"):
    if request.method == "POST" and "id_service" in request.form:
        id_service = int(request.form.get("id_service"))
        action = request.form.get("action")
        service_action(id_service, action)
    services = view_services(view)
    if view=="json":
        return services

    current_controller = set_current_controller({'title': 'Services', 'controller': 'services' })     
    return render_template("services.html", services=services, current_controller=current_controller)





@app.route("/users",methods=['GET', 'POST'])
def users(view="default"):
    if request.method == "POST" and "id_user" and "login" and "password" in request.form:
        user_data = {}
        user_data["id_user"] = int(request.form.get("id_user"))
        user_data["login"] = request.form.get("login")
        user_data["password"] = request.form.get("password")
        
        return json.dumps(save_user(user_data))

    if request.method == "POST" and "get_user" in request.form:
        id_user = int(request.form.get("get_user"))
        
        return json.dumps(get_user_data(id_user))

    if request.method == "POST" and "destroy_session" and "destroy_host" and "destroy_id_user" in request.form:
        id_user = int(request.form.get("destroy_id_user"))
        key = str(request.form.get("destroy_session"))
        host = str(request.form.get("destroy_host"))
        
        return json.dumps(destroy_session(id_user, key, host))

    users = view_users()

    current_controller = set_current_controller({'title': 'Users', 'controller': 'users' }) 
    return render_template("users.html", users=users, current_controller=current_controller)



@app.route("/configuration",methods=['GET', 'POST'])
@app.route("/configuration/<view>",methods=['GET', 'POST'])
def settings(view="system-tools"):
   
    if request.method == "POST" and "firefly_kill" in request.form:
        res = firefly_kill()
        
        return json.dumps(res)

    if len(view)>1:
        current_view = view    

    if current_view == "nx-settings":
       data = load_config_data('nx_settings', 'key')
    elif current_view == "system-tools":
       data = {} 
    elif current_view == "storages":
       data = load_config_data('nx_storages', 'title')
    elif current_view == "services":
       data = load_config_data('nx_services', 'title') 
    elif current_view == "views":
       data = load_config_data('nx_views', 'title')
    elif current_view == "channels":
       data = load_config_data('nx_channels', 'title') 
    else:
       data = {} 

    current_controller = set_current_controller({'title': 'Configuration', 'controller': 'configuration', 'current_view': current_view }) 
    return render_template("configuration.html", data=data, current_controller=current_controller)





@app.route("/login", methods=["POST"])
def login():
    current_controller = set_current_controller({'title': 'Login', 'controller': 'login' })         
    if request.method == "POST" and "username" in request.form:
        _user = auth_helper(request.form.get("username"), request.form.get("password"))
        if _user.is_authenticated():
            remember = request.form.get("remember", "no") == "yes"
            if login_user(_user, remember=remember):
                return render_template("index.html", current_controller=current_controller)
            else:
                flash("Sorry, but you could not log in.", "danger")
        else:
            flash("Login failed", "danger")

    return render_template("index.html", current_controller=current_controller)


@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    current_controller = set_current_controller({'title': 'Logout', 'controller': 'logout' }) 
    return render_template("index.html", current_controller=current_controller)
  


 
@app.route("/reports",methods=['GET', 'POST'])
@app.route("/reports/<view>",methods=['GET', 'POST'])
def reports(view=False):
    
    if view == False:
        plugins = AdmPlugins('reports')
        plugins.get_plugins()
        ctrl = ''
        template = "reports.html"
        env = plugins.env
    else:
        plugin = AdmPlugins('reports')
        plugin.env['get'] = request.args
        plugin.env['post'] = request.form
        
        ################################
        # CUSTOM LOADER
        plugin_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader(plugin.env['plugin_path']),
        ])
        app.jinja_loader = plugin_loader

        plugin.run(view)
        # ctrl = '/'+view
        ctrl = ''

        env = plugin.env

        template = plugin.env['plugin']['data']['template']
        
    current_controller = set_current_controller({'title': 'Reports', 'controller': 'reports'+ctrl }) 
    return render_template(template, view=view, env=env, current_controller=current_controller)


@app.route("/api/<view>",methods=['GET', 'POST'])
def api(view=False):
    
    type = 'reports'
    result = {'data': {}, 'status': False, 'reason': 'Plugin error' }

    if view != False:
        
        if request.method == "POST" and "plugin_type" in request.form:
           type = request.form.get("plugin_type")

        if request.method == "GET" and "plugin_type" in request.args:
           type = request.args.get("plugin_type")

        plugins = AdmPlugins(type)
        plugins.env['get'] = request.args
        plugins.env['post'] = request.form
        
        ################################
        # CUSTOM LOADER
    
        plugin_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader(plugins.env['plugin_path']),
        ])
        app.jinja_loader = plugin_loader

        plugins.api(view)

        result['data'] = plugins.env['plugin']
        result['status'] = True
        result['reason'] = 'Request sent'

        ctrl = '/'+view

    return json.dumps(result)





###############################
# GO

if __name__ == "__main__":
    app.run(host="0.0.0.0")
