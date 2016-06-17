#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nebula import *

import jinja2
import thread
import hashlib

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, make_response
from admin.auth import *


SECRET_KEY = "yeah, not actually a secret"
DEBUG = True

app = Flask(__name__,
        static_folder=os.path.join(nebula_root, "admin", "static"),
        template_folder=os.path.join(nebula_root, "admin", "templates")
        )
app.config.from_object(__name__)

login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"
login_manager.setup_app(app)


import logging as pylogging
log = pylogging.getLogger('werkzeug')
log.setLevel(pylogging.INFO)


@login_manager.user_loader
def load_user(id):
    return FlaskUser(int(id))


########################################################################
## APP TEMPLATE FILTERS

@app.template_filter('datetime')
def _jinja2_filter_datetime(date, format='%Y-%m-%d %H:%M:%S'):
    return str(time.strftime(format, time.localtime(date)))

@app.template_filter('date')
def _jinja2_filter_date(date, format='%Y-%m-%d'):
    return str(time.strftime(format, time.localtime(date)))

@app.template_filter('alert_icon')
def _jinja2_filter_alert_icon(str):

    icon = '<span class="glyphicon glyphicon-ok-sign"></span>'
    str = str.lower()

    if str == 'info':
        icon = '<span class="glyphicon glyphicon-info-sign"></span>'

    elif str == 'success':
        icon = '<span class="glyphicon glyphicon-ok-sign"></span>'

    elif str == 'warning':
        icon = '<span class="glyphicon glyphicon-warning-sign"></span>'

    elif str == 'danger':
        icon = '<span class="glyphicon glyphicon-ban-circle"></span>'

    return icon

@app.template_filter('bool_icon')
def _jinja2_filter_bool_icon(b):

    icon = '<span class="text-primary glyphicon glyphicon-ok-sign"></span><span class="sr-only">1</span>'

    if b == 'false':
        icon = '<span class="text-warning glyphicon glyphicon-ban-circle"></span><span class="sr-only">0</span>'

    return icon

@app.template_filter('starts_with')
def _jinja2_filter_starts_with(str, prefix):
    res = False
    if str.startswith(prefix):
        res = True

    return res

@app.template_filter('ACL')
def _jinja2_filter_ACL(token):
    res = False
    return acl_can(token, current_user)


########################################################################
## APP ROUTES

@app.route("/")
def index():
    current_controller = set_current_controller({'title': 'Dashboard', 'controller': 'dashboard', 'current_user': current_user })
    return render_template("index.html", current_controller=current_controller)


@app.route("/browser")
def browser():
    assets = view_browser()
    current_controller = set_current_controller({'title': 'Browser', 'controller': 'browser', 'current_user': current_user })
    return render_template("browser.html", assets=assets, current_controller=current_controller)


@app.route("/jobs", methods=['GET', 'POST'])
@app.route("/jobs/<view>", methods=['GET', 'POST'])
@app.route("/jobs/<view>/search", methods=['GET'])
@app.route("/jobs/<view>/search/<search>", methods=['GET'])
def jobs(view="active", search=""):

    acl = acl_can('can/job_control', current_user)

    jobs = []
    current_view = ''
    template = 'access.denied.html'

    if acl['status'] == True:

        template = 'job_monitor.html'

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

    current_controller = set_current_controller({'title': 'Jobs', 'current_view': current_view, 'controller': 'jobs', 'search': search, 'current_user': current_user, 'acl': acl })
    return render_template(template, jobs=jobs, current_controller=current_controller)




@app.route("/services",methods=['GET', 'POST'])
@app.route("/services/<view>",methods=['GET', 'POST'])
def services(view="default"):

    acl = acl_can('can/service_control', current_user)
    template = 'access.denied.html'
    services = {'now': int(time.time()), 'data': []}

    if acl['status'] == True:

        template = 'services.html'

        if request.method == "POST" and "id_service" in request.form and "action" in request.form:
            id_service = int(request.form.get("id_service"))
            action = request.form.get("action")
            service_action(id_service, action)

        if request.method == "POST" and "id_service" in request.form and "autostart" in request.form:
            id_service = int(request.form.get("id_service"))
            autostart = int(request.form.get("autostart"))
            service_autostart(id_service, autostart)

        services['data'] = view_services(view)
        services['now'] = int(time.time())

        if view=="json":
            return json.dumps(services)

    current_controller = set_current_controller({'title': 'Services', 'controller': 'services', 'current_user': current_user, 'acl': acl })
    return render_template(template, services=services, current_controller=current_controller)



@app.route("/configuration",methods=['GET', 'POST'])
@app.route("/configuration/<view>",methods=['GET', 'POST'])
@app.route("/configuration/<view>/<citem>",methods=['GET', 'POST'])
def settings(view="nx-settings", citem=-1):

    item = int(citem)
    data = {'status':False,'reason':'Total fail'}
    acl = acl_can('is_admin', current_user)
    template = 'access.denied.html'

    if len(view)>1:
        current_view = view

    current_controller = set_current_controller({'title': 'Configuration', 'controller': 'configuration', 'current_view': current_view, 'current_item': item, 'current_user': current_user, 'acl': acl })

    if acl['status'] == True:

        template = 'configuration.html'
        # API actions
        if current_view == 'api':
            data = {'status':False,'reason':'Api request bad','post': request.form }
            if request.method == "POST" and "destroy_session" and "destroy_host" and "destroy_id_user" in request.form:
                id_user = int(request.form.get("destroy_id_user"))
                key = str(request.form.get("destroy_session"))
                host = str(request.form.get("destroy_host"))
                data = destroy_session(id_user, key, host)
            if request.method == "POST" and "query_table" in request.form and request.form.get('query_table') == 'nx_users' and "query_data" in request.form:
                data = save_user_data(request.form.get('query_val'), request.form.get('query_data'))
            if request.method == "POST" and "query_table" in request.form and request.form.get('query_table') == 'nx_users' and "disable_confirm" in request.form:
                data = save_user_state(request.form.get('query_val'), request.form.get('disable_confirm'))
            if request.method == "POST" and "query_table" in request.form and "query_key" in request.form and "query_val" in request.form and "remove_confirm" in request.form:
                data = remove_config_data(request.form.get("query_table"), request.form.get("query_key"), request.form.get("query_val"))
            if request.method == "POST" and "query_table" in request.form and request.form.get('query_table') == 'nx_settings' and "query_data" in request.form:
                data = save_nx_settings(request.form.get('query_data'))
            if request.method == "POST" and "query_table" in request.form and "query_key" in request.form and "query_val" in request.form and "query_data" in request.form:
                data = save_config_data(request.form.get("query_table"), request.form.get("query_key"), request.form.get("query_val"), request.form.get('query_data'))


            return json.dumps(data)

        # STD view
        else:

            current_controller = set_current_controller({'title': 'Configuration', 'controller': 'configuration', 'current_view': current_view, 'current_item': item, 'current_user': current_user })

            if current_view == "nx-settings":

                if request.method == "POST" and "firefly_kill" in request.form:
                    res = firefly_kill()
                    return json.dumps(res)
                else:
                    flash("Double check input, settings validity is critical and this action can not be undone.", "warning")

                data = load_config_data('nx_settings', 'key')

            elif current_view == "system-tools":
                data = {}
            elif current_view == "storages":
                if item < 0:
                    data = load_config_data('nx_storages', 'title')
                else:
                    data = load_config_item_data('nx_storages', 'id_storage', item)
            elif current_view == "services":
                if item < 0:
                    data = load_config_data('nx_services', 'title')
                else:
                    data = load_config_item_data('nx_services', 'id_service', item)
            elif current_view == "views":
                if item < 0:
                    data = load_config_data('nx_views', 'title')
                else:
                    current_controller['user_data'] = view_users()
                    data = load_config_item_data('nx_views', 'id_view', item)
            elif current_view == "channels":
                if item < 0:
                    data = load_config_data('nx_channels', 'title')
                else:
                    data = load_config_item_data('nx_channels', 'id_channel', item)
            elif current_view == "actions":
                if item < 0:
                    data = load_config_data('nx_actions', 'title')
                else:
                    data = load_config_item_data('nx_actions', 'id_action', item)
            elif current_view == "users":
                if item < 0:
                    data = view_users()
                else:
                    data = get_user_data(item)
            else:
                data = {}

    return render_template(template, data=data, current_controller=current_controller)





@app.route("/login", methods=["POST"])
def login():
    current_controller = set_current_controller({'title': 'Login', 'controller': 'login', 'current_user': current_user })
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
    current_controller = set_current_controller({'title': 'Logout', 'controller': 'logout', 'current_user': current_user })
    return render_template("index.html", current_controller=current_controller)




@app.route("/reports",methods=['GET', 'POST'])
@app.route("/reports/<view>",methods=['GET', 'POST'])
def reports(view=False):
    acl = acl_can('can/export', current_user)
    template = 'access.denied.html'
    ctrl = ''
    env = {}

    if acl['status'] == True:
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

            plugin_loader = jinja2.ChoiceLoader([
                app.jinja_loader,
                jinja2.FileSystemLoader(plugin.env['plugin_path']),
                ])
            app.jinja_loader = plugin_loader

            try:
                logging.info("{} executes plugin {}".format(current_user.name, plugin.env["plugin_name"]))
                plugin.run(view)
                ctrl = ''
                env = plugin.env
                template = plugin.env['plugin']['data']['template']
                logging.debug("Plugin {} execution finished".format(plugin.env["plugin_name"]))
            except Exception, e:
                template = 'plugin.error.html'
                plugin.env['errors']['plugin_error'] = log_traceback("Plugin error")

    current_controller = set_current_controller({'title': 'Reports', 'controller': 'reports'+ctrl, 'current_user': current_user, 'acl': acl })
    return render_template(template, view=view, env=env, current_controller=current_controller)


@app.route("/api",methods=['GET', 'POST'])
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


@app.route('/download',methods=['GET', 'POST'])
@app.route('/download/<file_name>',methods=['GET', 'POST'])
def download(file_name='<no file>'):

    download_dir = '/tmp'
    raw_data = "Download file {} not found".format(file_name)
    response = make_response(raw_data)
    response.headers["Content-type"] = "text/plain"

    download_path = download_dir + '/' + file_name

    if os.path.exists(download_path) and os.path.isfile(download_path):

        raw = open(download_path, 'r+b')
        raw_data = raw.read()

        # Flask magic begins :D
        response = make_response(raw_data)

        # Set the right header for the responseto be downloaded, instead of just printed on the browser
        response.headers["Content-Disposition"] = "attachment; filename="+file_name
        response.headers["Content-type"] = "text/plain"

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0")
