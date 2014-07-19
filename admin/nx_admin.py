import sys

NX_ROOT = sys.argv[1]
if not NX_ROOT in sys.path:
    sys.path.append(NX_ROOT)

from nx import *
from nx.objects import Asset







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


def view_jobs(view=""):
    db = DB()
    cols = [ "id_job", "id_object", "id_action", "settings", "id_service", "priority", "progress", "retries", "ctime", "stime", "etime", "message", "id_user", "action_title", "asset_title" ]

    if view == "failed":
        cond = " AND j.progress = -3"
    elif view == "completed":
        cond = " AND j.progress = -2"
    else:
        cond = " AND (j.progress >= -1 OR {} - etime < 60)".format(time.time())

    db.query("""SELECT j.id_job, j.id_object, j.id_action, j.settings, j.id_service, j.priority, j.progress, j.retries, j.ctime, j.stime, j.etime, j.message, j.id_user, a.title 
        FROM nx_jobs as j, nx_actions as a WHERE a.id_action = j.id_action{} ORDER BY etime DESC, stime DESC, ctime DESC """.format(cond))

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
    db = DB()
    id_job = id_job
    db.query("UPDATE nx_jobs set id_service=0, progress=-1, retries=0, ctime=%s, stime=0, etime=0, message='Pending', id_user=%s WHERE id_job=%s", (time.time(), id_user, id_job))
    db.commit()
