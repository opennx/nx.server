#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import thread
import hashlib

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from auth import *

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)


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


@app.route("/browser")
def browser():
    assets = view_browser()
    return render_template("browser.html", assets=assets)


 
@app.route("/jobs", methods=['GET', 'POST'])
@app.route("/jobs/<view>", methods=['GET', 'POST'])
def jobs(view="active"):
    if request.method == "POST" and "id_job" in request.form:
        id_job = int(request.form.get("id_job"))
        job_action(id_job, "restart", id_user=current_user.id)
        flash("Job {} restarted".format(id_job), "info")

    if view == "failed":
        current_view = "failed"
    elif view == "completed":
        current_view = "completed"
    elif view == "json":
        current_view = "json"
    else:
        current_view = "active"

    jobs = view_jobs(current_view)
    if view=="json":
        return jobs
    return render_template("job_monitor.html", jobs=jobs, current_view=current_view)




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
    return render_template("services.html", services=services)





@app.route("/users",methods=['GET', 'POST'])
def users(view="default"):
    if request.method == "POST" and "id_user" in request.form:
        user_data = {}

        user_data["id_user"] = int(request.form.get("id_user"))
        user_data["login"] = request.form.get("login")
        user_data["password"] = request.form.get("password")
        
        return json.dumps(save_user(user_data))

    users = view_users()
    return render_template("users.html", users=users)





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
  


 



if __name__ == "__main__":
    app.run(host="0.0.0.0")