#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread
import hashlib

from nx import *
from nx.assets import Asset

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify

from auth import *



 
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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

@login_manager.user_loader
def load_user(id):
    return flask_users.get(int(id))





@app.route("/")
def index():
    return render_template("index.html")

 
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

    return render_template("job_monitor.html", jobs=jobs, current_view=current_view)




@app.route("/services",methods=['GET', 'POST'])
@app.route("/services/<view>")
def services(view="default"):
    cols = ["id_service", "agent", "title", "host", "autostart", "loop_delay", "settings", "state", "pid", "last_seen"]
    db = DB()

    if request.method == "POST" and "id_service" in request.form:
        id_service = int(request.form.get("id_service"))
        sstate = {
            "stop" : 3,
            "start" : 2
            }[request.form.get("action")]
        db.query("UPDATE nx_services set state = %s WHERE id_service=%s", [sstate, id_service])
        db.commit()
        return "OK"



    db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services ORDER BY id_service ASC")

    if view=="json":
        services={}
        for sdata in db.fetchall():
            services[str(sdata[0])] = sdata[7]
        return jsonify(**services)

    services = []
    for service_data in db.fetchall():
        service = {}
        for i, c in enumerate(cols):
            service[c] = service_data[i]
        services.append(service)
    return render_template("services.html", services=services)









@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        id_user = auth_helper(request.form.get("username"), request.form.get("password"))
        if id_user:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(flask_users[id_user], remember=remember):
                return render_template("index.html")
            else:
                flash("Sorry, but you could not log in.", "danger")
        else:
            flash("Login failed", "danger")
    return render_template("index.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    return render_template("index.html")
  


 




class Service(ServicePrototype):
    def on_init(self):
        try:
            thread.start_new_thread(app.run(host="0.0.0.0"))
        except:
            logging.info("Flask reload...")

    def on_main(self):
        pass