#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread
import hashlib

from nx import *
from nx.assets import Asset

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, 
                            confirm_login, fresh_login_required)
 
config["users"] = {
        1 : {
        "login" : "admin",
        "password" : "21232f297a57a5a743894a0e4a801fc3", 
        }
    }

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = config["users"][id]["login"]
        self.active = True

    def is_active(self):
        return self.active

class Anonymous(UserMixin):
    name = u"Anonymous"
    id = 0
    def is_authenticated(self):
        return False

flask_users = {}
for id_user in config["users"]:
    flask_users[id_user] = User(id_user)

def login_to_id(login):
    for id_user in config["users"]:
        if config["users"][id_user]["login"] == login:
            return id_user
    else:
        return False

def auth_helper(login, password):
    for id_user in config["users"]:
        if config["users"][id_user]["login"] == login:
            if config["users"][id_user]["password"] == hashlib.md5(password.encode()).hexdigest():
                return id_user
            else:
                print ("Invalid password", config["users"][id_user]["password"], hashlib.md5(password.encode()).hexdigest())
                return False
    else:
        print ("No such user")
        return False

 
SECRET_KEY = "yeah, not actually a secret"
DEBUG = True
 

app = Flask(__name__)
app.config.from_object(__name__)

login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"
login_manager.setup_app(app)



def get_navigation(id_user):
    return [
        ("Jobs", "/jobs"),
        ("Services", "/services"),
        ("Logout","/logout")
    ]


@login_manager.user_loader
def load_user(id):
    return flask_users.get(int(id))



@app.route("/")
def index():
    return render_template("index.html", navigation=get_navigation(current_user.id))
 
@app.route("/jobs", methods=['GET', 'POST'])
@app.route("/jobs/<view>", methods=['GET', 'POST'])
def jobs(view="active"):
    cols = [ "id_job", "id_object", "id_action", "settings", "id_service", "priority", "progress", "retries", "ctime", "stime", "etime", "message", "id_user", "action_title", "asset_title" ]

    if view == "failed":
        current_view = "failed"
        cond = " AND j.progress = -3"
    elif view == "completed":
        current_view = "completed"
        cond = " AND j.progress = -2"
    else:
        current_view = "active"
        cond = " AND (j.progress >= -1 OR {} - etime < 60)".format(time.time())

    db = DB()
    if request.method == "POST" and "id_job" in request.form:
        id_job = int(request.form.get("id_job"))
        db.query("UPDATE nx_jobs set id_service=0, progress=-1, retries=0, ctime=%s, stime=0, etime=0, message='Pending', id_user=%s WHERE id_job=%s", (time.time(), current_user.id, id_job))
        db.commit()
        flash("Job {} restarted".format(id_job), "info")

    db.query("""SELECT j.id_job, j.id_object, j.id_action, j.settings, j.id_service, j.priority, j.progress, j.retries, j.ctime, j.stime, j.etime, j.message, j.id_user, a.title 
        FROM nx_jobs as j, nx_actions as a WHERE a.id_action = j.id_action{} ORDER BY etime DESC, stime DESC, ctime DESC """.format(cond))

    if view=="json":
        jobs = {}
        for job_data in db.fetchall():
            jobs[str(job_data[0])] = [job_data[6], job_data[11]]
        return jsonify(**jobs)

    jobs = []
    for job_data in db.fetchall():
        asset = Asset(job_data[1])
        job_data = list(job_data)
        job_data.append(asset["title"])
        job = {}
        for i,c in enumerate(cols):
            job[c] = job_data[i]
        jobs.append(job)

    return render_template("job_monitor.html", navigation=get_navigation(current_user.id), jobs=jobs, current_view=current_view)




@app.route("/services")
def services():
    cols = ["id_service", "agent", "title", "host", "autostart", "loop_delay", "settings", "state", "pid", "last_seen"]
    db = DB()
    db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services ORDER BY id_service ASC")
    services = []
    for service_data in db.fetchall():
        service = {}
        for i, c in enumerate(cols):
            service[c] = service_data[i]
        services.append(service)
    return render_template("services.html", navigation=get_navigation(current_user.id), services=services)









@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        id_user = auth_helper(request.form.get("username"), request.form.get("password"))
        if id_user:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(flask_users[id_user], remember=remember):
                return render_template("index.html", navigation=get_navigation(current_user.id))
            else:
                flash("Sorry, but you could not log in.", "danger")
        else:
            flash("Login failed", "danger")
    return render_template("index.html", navigation=get_navigation(current_user.id))


@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    return render_template("index.html", navigation=get_navigation(current_user.id))
  









class Service(ServicePrototype):
    def on_init(self):
        thread.start_new_thread(app.run(host="0.0.0.0"))

    def on_main(self):
        db = DB()
        db.query("SELECT id_service, state, last_seen FROM nx_services")
        service_status = db.fetchall()
        messaging.send("hive_heartbeat", {"service_status": service_status})
