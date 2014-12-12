import sys
reload(sys)
sys.setdefaultencoding('utf-8')

NX_ROOT = sys.argv[1]
if not NX_ROOT in sys.path:
    sys.path.append(NX_ROOT)

from nx import *
from nx.objects import *



########################################################################
## Misc tools

def set_current_controller(data={}):
    if 'title' in data:
       data['title'] = data['title']+' | OpenNX'
    else:
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
            services[str(sdata[0])] = sdata[7]
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
        "start" : 2
        }[action]
    db.query("UPDATE nx_services set state = %s WHERE id_service=%s", [sstate, id_service])
    db.commit()
    return "OK"

## Services administration
########################################################################
##


def view_jobs(view="", search=""):
    db = DB()
    cols = [ "id_job", "id_object", "id_action", "settings", "id_service", "priority", "progress", "retries", "ctime", "stime", "etime", "message", "id_user", "action_title", "asset_title" ]

    sql_join = ""

    if view == "failed":
        cond = " AND j.progress = -3"
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
        WHERE a.id_action = j.id_action{} ORDER BY etime DESC, stime DESC, ctime DESC """.format(cond))

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
        db.query("SELECT id_object FROM nx_users")
        
        for id_object, in db.fetchall():
            user = User(id_object, db=db)
            user["ctime_human"] = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user["ctime"]))) 
            user["mtime_human"] = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user["mtime"]))) 
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

    try: 
        db.query("SELECT key, id_user, host, ctime, mtime FROM nx_sessions WHERE id_user = "+str(id_user)+" ORDER BY mtime")
        
        user["sessions"] = []

        for s in db.fetchall():
            
            session = {}

            session["key"] = s[0] 
            session["id_user"] = s[1]
            session["host"] = s[2]
            session["ctime_human"] = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s[3]))) 
            session["mtime_human"] = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s[4]))) 
            
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
        db.query("DELETE FROM nx_sessions WHERE id_user = "+str(id_user)+" AND key LIKE '"+str(key)+"' AND host LIKE '"+str(host)+"' ")
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
## Dashboard tools, loaders

def load_storages():

    db = DB()
    
    result = {'storages': [], 'status': True, 'reason': 'Storages loaded'}

    try: 
        db.query("SELECT * FROM nx_storages ORDER BY title")
        
        for storage in db.fetchall():
            result['storages'].append(storage)
        
    except: 

        result['status'] = False
        result['reason'] = 'Storages not loaded, database error'

    return result         


def load_settings():

    db = DB()
    
    result = {'settings': [], 'status': True, 'reason': 'Settings loaded'}

    try: 
        db.query("SELECT * FROM nx_settings ORDER BY key")
        
        for storage in db.fetchall():
            result['settings'].append(storage)
        
    except: 

        result['status'] = False
        result['reason'] = 'Settings not loaded, database error'

    return result             


def load_services():

    db = DB()
    
    result = {'services': [], 'status': True, 'reason': 'Services loaded'}

    try: 
        db.query("SELECT * FROM nx_services ORDER BY title")
        
        for storage in db.fetchall():
            result['services'].append(storage)
        
    except: 

        result['status'] = False
        result['reason'] = 'Services not loaded, database error'

    return result             


def load_views():

    db = DB()
    
    result = {'views': [], 'status': True, 'reason': 'Views loaded'}

    try: 
        db.query("SELECT * FROM nx_views ORDER BY title")
        
        for storage in db.fetchall():
            result['views'].append(storage)
        
    except: 

        result['status'] = False
        result['reason'] = 'Views not loaded, database error'

    return result                 

def load_channels():

    db = DB()
    
    result = {'channels': [], 'status': True, 'reason': 'Channels loaded'}

    try: 
        db.query("SELECT * FROM nx_channels ORDER BY title")
        
        for storage in db.fetchall():
            result['channels'].append(storage)
        
    except: 

        result['status'] = False
        result['reason'] = 'Channels not loaded, database error'

    return result                 
