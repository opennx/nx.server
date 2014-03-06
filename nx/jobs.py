#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

MAX_RETRIES = 3

class Job():
    def __init__(self, id_service,  actions=[]):

        qactions = ", ".join([str(k) for k in actions])
    
        self.id_job    = False
        self.id_object = False
        self.id_action = False
        self.settings  = False
        self.retries   = False

        db = DB()
        db.query("""UPDATE nx_jobs 
            SET id_service = {id_service},
                stime      = {stime},
                etime      = 0
            WHERE 
                id_job IN (SELECT id_job from nx_jobs
                    WHERE progress   = -1
                    AND   id_service IN (0, {id_service})
                    AND   id_action  IN ({actions})
                    AND   retries    <  {max_retries}

                    ORDER BY priority DESC, ctime DESC LIMIT 1
                    )
                  """.format(
                      stime       = time.time(),
                      id_service  = id_service, 
                      actions     = qactions, 
                      max_retries = MAX_RETRIES
                      )
            )

        db.commit()

        db.query("""SELECT id_job, id_object, id_action, settings, priority, retries FROM nx_jobs 
            WHERE progress = -1 
            AND id_service={id_service}
            """.format(id_service=id_service)
            )


        for id_job, id_object, id_action, settings, priority, retries in db.fetchall():
            logging.debug("New job found")
            self.id_job    = id_job
            self.id_object = id_object
            self.id_action = id_action
            self.settings  = settings
            self.priority  = priority
            self.retries   = retries
            break
        #else:
        #    logging.debug("No new job")




    def __len__(self):
        return bool(self.id_job)

    def set_progress(self, progress, message="In progress"):
        db = DB()
        db.query("""UPDATE nx_jobs
            SET progress  = {progress}, 
                message   = '{message}'
            WHERE 
                id_job = {id_job}
            """.format(
                    progress = progress,
                    message  = message,
                    id_job  = self.id_job
                    )
                )
        db.commit()



    def abort(self):
        db = DB()


    def restart(self):
        db = DB()


    def fail(self, message="Failed"):
        db = DB()
        db.query("""UPDATE nx_jobs
            SET retries   = {retries}, 
                priority  = {priority}, 
                progress  = -3
                message   = '{message}'
            WHERE 
                id_job  = {id_job}
            """.format(
                    retries  = self.retries+1, 
                    priority = max(0,self.priority-1),
                    message  = message,
                    id_job   = self.id_job
                    )
                )
        db.commit()
        logging.error("Job ID {} : {}".format(self.id_job, message))


    def done(self, message="Completed"):
        db = DB()
        db.query("""UPDATE nx_jobs
            SET   
                progress  = -2,
                etime     = {etime},
                message   = '{message}'
            WHERE 
                id_job  = {id_job}
            """.format(
                    etime   = time.time(), 
                    message = message,
                    id_job  = self.id_job
                    )
                )
        db.commit()
        logging.goodnews("Job ID {} : {}".format(self.id_job, message))