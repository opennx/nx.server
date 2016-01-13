from nx import *
from nx.objects import User, get_user

from .nx_admin import *

from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin,
                            confirm_login, fresh_login_required)
import hashlib

class FlaskUser(UserMixin):
    def __init__(self, id):
        if type(id) == User:
            self._data = id
            self.id = self._data.id
        else:
            self._data = User(id)
            self.id = id

    def is_active(self):
        return self.active

    @property
    def name(self):
        return self._data["login"]

    def is_authenticated(self):
        return bool(self.id)

    def is_active(self):
        return True

    def is_admin(self):
        return self._data["is_admin"]

    def is_disabled(self):
        return self._data["is_disabled"]

    def has_right(self, key, value=True):
        return self._data.has_right(key, value)




class Anonymous(UserMixin):
    name = u"Anonymous"
    id = 0

    def is_admin(self):
        return 'false'

    def is_disabled(self):
        return 'true'

    def is_authenticated(self):
        return False


def auth_helper(login, password):
    user = get_user(login, password)
    if user:
        return FlaskUser(user)
    else:
        return Anonymous()
