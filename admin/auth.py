from nx_admin import *

from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, 
                            confirm_login, fresh_login_required)
import hashlib

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
                return False
    else:
        print ("No such user")
        return False
