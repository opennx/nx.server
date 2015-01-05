import sys
import imp

reload(sys)
sys.setdefaultencoding('utf-8')

NX_ROOT = sys.argv[1]
if not NX_ROOT in sys.path:
	sys.path.append(NX_ROOT)

from nx import *
from nx.objects import *

from flask import request, url_for
import os

from nx.plugins import plugin_path
if plugin_path:
	python_plugin_path = os.path.join(plugin_path, "python")
	if os.path.exists(python_plugin_path):
		sys.path.append(python_plugin_path)


########################################################################
## Misc tools

def set_current_controller(data={}):

	if 'title' in data:
	   data['sub_title'] = data['title']
	   data['title'] = data['title']+' | OpenNX'
	else:
	   data['sub_title'] = 'OpenNX'
	   data['title'] = 'OpenNX'
	return data


def firefly_kill():
	try:
		messaging.send("firefly_shutdown")
		res = {'status': True, 'reason': 'Ok', 'description': 'Everything went ok'}
	except:
		res = {'status': False, 'reason': 'Failed', 'description': 'Request failed' }
	return res


########################################################################
## Assets


def view_browser():
	db=DB()
	result = []
	db.query("SELECT id_object FROM nx_assets ORDER BY ctime DESC")
	for id_object, in db.fetchall():
		asset = Asset(id_object, db=db)
		result.append(asset)
	return result

########################################################################
## Services administration

def view_services(view=""):
	db = DB()
	cols = ["id_service", "agent", "title", "host", "autostart", "loop_delay", "settings", "state", "pid", "last_seen"]
	db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services ORDER BY id_service ASC")
	if view=="json":
		services={}
		for sdata in db.fetchall():
			services[str(sdata[0])] = sdata
		return json.dumps(services)
	services = []
	for service_data in db.fetchall():
		service = {}
		for i, c in enumerate(cols):
			service[c] = service_data[i]
		services.append(service)
	return services

def service_action(id_service, action):
	db = DB()
	sstate = {
		"stop" : 3,
		"start" : 2,
		"kill" : 4
		}[action]
	db.query("UPDATE nx_services set state = %s WHERE id_service=%s", [sstate, id_service])
	db.commit()
	return "OK"

def service_autostart(id_service, autostart):
	db = DB()
	db.query("UPDATE nx_services set autostart = %s WHERE id_service=%s", [autostart, id_service])
	db.commit()
	return "OK"


########################################################################
## Jobs administration

def view_jobs(view="", search=""):
	db = DB()
	cols = [ "id_job", "id_object", "id_action", "settings", "id_service", "priority", "progress", "retries", "ctime", "stime", "etime", "message", "id_user", "action_title", "asset_title" ]

	sql_join = ""

	if view == "failed":
		cond = " AND (j.progress = -3 OR j.progress = -4)"
	elif view == "completed":
		cond = " AND j.progress = -2"
	else:
		cond = " AND (j.progress >= -1 OR {} - etime < 60)".format(time.time())

	if len(search)>1:

		sql_join = """ JOIN nx_meta as m ON m.id_object = j.id_object """

		cond = cond + """ AND m.tag IN(SELECT tag FROM nx_meta_types WHERE searchable = 1)
				AND lower(unaccent(m.value)) LIKE lower(unaccent('%"""+search.encode('utf-8').strip()+"""%')) """

	db.query("""SELECT j.id_job, j.id_object, j.id_action, j.settings, j.id_service, j.priority, j.progress, j.retries, j.ctime, j.stime, j.etime, j.message, j.id_user, a.title
		FROM nx_jobs as j
		JOIN nx_actions as a ON a.id_action = j.id_action
		"""+sql_join+"""
		WHERE a.id_action = j.id_action {} ORDER BY stime DESC, etime DESC, ctime DESC """.format(cond))

	if view=="json":
		jobs = {}
		for job_data in db.fetchall():
			jobs[str(job_data[0])] = [job_data[6], job_data[11]]
		return json.dumps(jobs)

	jobs = []
	for job_data in db.fetchall():
		asset = Asset(job_data[1])
		job_data = list(job_data)
		job_data.append(asset["title"])
		job = {}
		for i,c in enumerate(cols):
			job[c] = job_data[i]
		jobs.append(job)

	return jobs



def job_action(id_job, action, id_user=0):

	result = {'status': True, 'reason': 'Job action set'}

	try:
		# abort -> don't modify stime
		db = DB()
		id_job = id_job
		db.query("UPDATE nx_jobs set id_service=0, progress=%s, retries=0, ctime=%s, stime=0, etime=0, message='Pending', id_user=%s WHERE id_job=%s", (action, time.time(), id_user, id_job))
		db.commit()

	except:

		result['status'] = False
		result['reason'] = 'Users not loaded, database error'

	return result



########################################################################
## Users administration

def view_users():

	db = DB()

	result = {'users': [], 'status': True, 'reason': 'Users loaded'}

	try:
		db.query("SELECT id_object FROM nx_users ORDER BY login")

		for id_object, in db.fetchall():
			user = User(id_object, db=db)
			result['users'].append(user)

	except:

		result['status'] = False
		result['reason'] = 'Users not loaded, database error'

	return result


def get_user_data(id_user):

	db = DB()

	user = {}
	_user = User(id_user, db=db)
	user["meta"] = _user.meta

	format='%Y-%m-%d %H:%M:%S'

	try:
		db.query("SELECT key, id_user, host, ctime, mtime FROM nx_sessions WHERE id_user = %s ORDER BY mtime", [id_user])

		user["sessions"] = []

		for s in db.fetchall():

			session = {}

			session["key"] = s[0]
			session["id_user"] = s[1]
			session["host"] = s[2]
			session["ctime_human"] = str(time.strftime(format, time.localtime(s[3])))
			session["mtime_human"] = str(time.strftime(format, time.localtime(s[4])))

			user["sessions"].append(session)

		user['status'] = True
		user['reason'] = 'User loaded'

	except:

		user['status'] = False
		user['reason'] = 'User not found'

	return user



def destroy_session(id_user, key, host):

	db = DB()

	result = {'id_user': id_user, 'status': True, 'reason': 'Session destroyed' }

	try:
		db.query("DELETE FROM nx_sessions WHERE id_user = %s AND key LIKE %s AND host LIKE %s ", [id_user, key, host])
		db.commit()
	except:
		result["status"] = False
		result["reason"] = "Session destroy, query failed"

	return result



def save_user(user_data):

	result = {'status': True, 'reason': 'User saved'}

	user = User(user_data['id_user'])
	user['login'] = user_data['login']
	user.set_password(user_data['password'])

	user.save()
	return result


########################################################################
## Config tools, loaders, savers, hackers and horses

def save_config_data(query_table, query_key, query_val, query_data):
	db = DB()

	result = {'data': {}, 'status': True, 'reason': 'Data loaded'}

	result['data']['query_data'] = query_data

	try:

		keys = []
		vals = []
		update = []

		for key, val in json.loads(query_data).iteritems():
			keys.append(str(key))
			vals.append(str(val))
			update.append( str(key)+" =  '"+str(val)+"'"  )

		if query_val == 0:
			sql_query = "INSERT INTO ("+str(','.join(keys))+") VALUES ('"+str("','".join(vals))+"')"
		else:
			sql_query = "UPDATE "+str(query_table)+" SET "+str(','.join(update))+" WHERE "+str(query_key)+" = '"+str(query_val)+"'"

		# db.query(sql_query)
		result['data']['query'] = sql_query
	except Exception, e:

		result['status'] = False
		result['reason'] = 'Data not loaded, database error ' + format(e)

	return result



def load_config_data(query_table, query_order):

	db = DB()

	result = {'data': [], 'status': True, 'reason': 'Data loaded'}

	try:
		db.query("SELECT * FROM "+str(query_table)+" ORDER BY "+str(query_order))

		for item in db.fetchall():
			result['data'].append(item)

	except:

		result['status'] = False
		result['reason'] = 'Data not loaded, database error'

	return result


def load_config_item_data(query_table, column, id):

	db = DB()

	result = {'data': [], 'status': True, 'reason': 'Data loaded'}

	try:
		db.query("SELECT * FROM "+str(query_table)+" WHERE "+str(column)+" = "+str(id))

		res = db.fetchall()

		if len(res) == 1:
			result['data'] = res[0]

	except:

		result['status'] = False
		result['reason'] = 'Data not loaded, database error'

	return result



#########################################################################
## PLUGIN LOADER

class AdmPlugins():
	def __init__(self, type='reports', name=''):

		self.env = {}

		self.env['plugin_name']  = name
		self.env['plugin'] = {}
		self.env['plugin_path'] = ''
		self.env['plugins_available'] = {}
		self.env['errors'] = {}
		self.env['template']  = ''

		if plugin_path:
			self.env['plugin_path'] = os.path.join(plugin_path, type)


	def get_plugins(self):

		if not os.path.exists(self.env['plugin_path']):
			self.env['errors']['plugin_path'] = "Admin plugins directory does not exist"

		else:
			for fname in os.listdir(self.env['plugin_path']):

				mod_name, file_ext = os.path.splitext(fname)

				if file_ext != ".py":
					continue

				try:

					plugin = imp.load_source(mod_name, os.path.join(self.env['plugin_path'], fname))

					if not "__manifest__" in dir(plugin):
						self.env['errors'][mod_name] = "No plugin manifest found in {}".format(fname)
						continue

					self.env['plugins_available'][mod_name] = {'manifest': plugin.__manifest__, 'path': os.path.join(self.env['plugin_path'], fname), 'data': plugin}

				except:

					self.env['errors'][mod_name] = 'Error while openning file {}'.format(fname)



	def run(self, mod_name):

		if not os.path.exists(self.env['plugin_path']):
			self.env['errors']['plugin_path'] = "Admin plugins directory does not exist"

		else:

			try:

				plugin = imp.load_source(mod_name, os.path.join(self.env['plugin_path'], mod_name+'.py'))

				if not "__manifest__" in dir(plugin):
					self.env['errors'][mod_name] = "No plugin manifest found in {}".format(mod_name)
				else:

					import importlib

					plugin_i = importlib.import_module(mod_name)

					plugin_class = plugin_i.Plugin()
					plugin_class.run()

					self.env['plugin'] = {'manifest': plugin.__manifest__, 'dir': self.env['plugin_path'], 'path': os.path.join(self.env['plugin_path'], mod_name+'.py'), 'token': mod_name, 'src': plugin,'data': plugin_class.env}

			except Exception, e:

				self.env['errors'][mod_name] = 'Error while openning file {}'.format(os.path.join(self.env['plugin_path'], mod_name+'.py'))
				self.env['errors']['Exception'] = format(e)
				self.env['errors']['Args'] = 'GET: ' + json.dumps(self.env['get']) + ' POST: ' + json.dumps(self.env['post'])



	def api(self, mod_name):

		if not os.path.exists(self.env['plugin_path']):
			self.env['errors']['plugin_path'] = "Admin plugins directory does not exist"

		else:

			try:

				plugin = imp.load_source(mod_name, os.path.join(self.env['plugin_path'], mod_name+'.py'))

				if not "__manifest__" in dir(plugin):
					self.env['errors'][mod_name] = "No plugin manifest found in {}".format(mod_name)
				else:

					import importlib

					plugin_i = importlib.import_module(mod_name)

					plugin_class = plugin_i.Plugin()
					plugin_class.api()

					self.env['plugin'] = plugin_class.api()

			except Exception, e:

				self.env['errors'][mod_name] = 'Error while openning file {}'.format(os.path.join(self.env['plugin_path'], mod_name+'.py'))
				self.env['errors']['Exception'] = format(e)
				self.env['errors']['Args'] = 'GET: ' + json.dumps(self.env['get']) + ' POST: ' + json.dumps(self.env['post'])


