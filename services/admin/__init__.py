#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
import thread
import hashlib

from flask import Flask, request, render_template, redirect, url_for, flash
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
 
@app.route("/jobs")
def jobs():
    cols = ["id_service", "agent", "title", "host"]
    db = DB()
    db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services")
    for id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen in db.fetchall():
        pass
    return render_template("job_monitor.html", navigation=get_navigation(current_user.id))

@app.route("/services")
def services():
    return render_template("services.html", navigation=get_navigation(current_user.id))


@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        id_user = auth_helper(request.form.get("username"), request.form.get("password"))
        if id_user:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(flask_users[id_user], remember=remember):
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Sorry, but you could not log in.", "danger")
        else:
            flash("Login failed", "danger")

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("index"))
  




class Service(ServicePrototype):
    def on_init(self):
        thread.start_new_thread(app.run(host="0.0.0.0"))

    def on_main(self):
        db = DB()
        db.query("SELECT id_service, state, last_seen FROM nx_services")
        service_status = db.fetchall()
        messaging.send("hive_heartbeat", {"service_status": service_status})
