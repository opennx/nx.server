#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
import thread

from flask import Flask, request, render_template, redirect, url_for, flash
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, 
                            confirm_login, fresh_login_required)
 
class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active
 
    def is_active(self):
        return self.active
 
 
class Anonymous(UserMixin):
    name = u"Anonymous"
    def is_authenticated(self):
        return False
 
USERS = {
    1: User(u"Notch", 1),
    2: User(u"Steve", 2),
    3: User(u"Creeper", 3, False),
}
 
USER_NAMES = dict((u.name, u) for u in USERS.itervalues())
 
 
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
    return USERS.get(int(id))

@app.route("/")
def index():
    return render_template("index.html")
 
 
def job_monitor():
    cols = ["id_service", "agent", "title", "host"]
    db = DB()
    db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services")
    for id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen in db.fetchall():
        pass

    return render_template("job_monitor.html")


@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        if username in USER_NAMES:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(USER_NAMES[username], remember=remember):
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))
  

@app.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    if request.method == "POST":
        confirm_login()
        flash(u"Reauthenticated.")
        return redirect(request.args.get("next") or url_for("index"))
    return render_template("reauth.html")






class Service(ServicePrototype):
    def on_init(self):
        thread.start_new_thread(app.run(host="0.0.0.0"))

    def on_main(self):
        db = DB()
        db.query("SELECT id_service, state, last_seen FROM nx_services")
        service_status = db.fetchall()
        messaging.send("hive_heartbeat", {"service_status": service_status})
