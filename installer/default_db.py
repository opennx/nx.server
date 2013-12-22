SQLITE_TPL = [

"""CREATE TABLE "nx_assets" ( 
    "id_asset" integer primary key NOT NULL, 
    "media_type" integer NOT NULL, 
    "content_type" integer NOT NULL, 
    "id_folder" integer NOT NULL, 
    "ctime" integer NOT NULL, 
    "mtime" integer NOT NULL, 
    "origin" text NOT NULL, 
    "version_of" integer NOT NULL, 
    "status" integer NOT NULL
)""",

"""CREATE TABLE "nx_folders" ( 
    "id_folder" integer primary key NOT NULL, 
    "title" text NOT NULL, 
    "color" integer NOT NULL
);""",

"""CREATE TABLE "nx_meta" ( 
    "id_asset" integer NOT NULL, 
    "tag" text NOT NULL, 
    "value" text NOT NULL,  
    PRIMARY KEY ("id_asset", "tag")
);""",

"""CREATE TABLE "nx_meta_types" ( 
    "namespace" text NOT NULL, 
    "tag" text NOT NULL, 
    "editable" integer NOT NULL, 
    "searchable" integer NOT NULL, 
    "class" integer NOT NULL, 
    "default_value" text NOT NULL, 
    "settings" text NOT NULL,  
    PRIMARY KEY ("tag")
);""",

"""CREATE TABLE "nx_meta_aliases" ( 
    "tag" text NOT NULL, 
    "lang" text NOT NULL, 
    "alias" text NOT NULL,  
    PRIMARY KEY ("tag", "lang")
);""",





"""CREATE TABLE "nx_settings" ( 
    "key" text NOT NULL, 
    "value" text NOT NULL,  
    PRIMARY KEY ("key")
);""",

"""CREATE TABLE "nx_storages" ( 
    "id_storage" integer primary key NOT NULL, 
    "title" text NOT NULL, 
    "protocol" integer NOT NULL, 
    "path" text NOT NULL, 
    "login" text NOT NULL, 
    "password" text NOT NULL
);""",

"""CREATE TABLE "nx_services" ( 
    "id_service" integer primary key NOT NULL, 
    "agent" text NOT NULL, 
    "title" text NOT NULL, 
    "host" text NOT NULL, 
    "autostart" integer NOT NULL, 
    "loop_delay" integer NOT NULL, 
    "settings" text NULL, 
    "state" integer NOT NULL, 
    "pid" integer NOT NULL, 
    "last_seen" integer NOT NULL
);""",





"""CREATE TABLE "nx_jobs" ( 
    "id_asset" integer NOT NULL, 
    "id_action" integer NOT NULL, 
    "settings" text NOT NULL DEFAULT '{}', 
    "priority" integer NOT NULL, 
    "ctime" integer NOT NULL, 
    "stime" integer NOT NULL, 
    "etime" integer NOT NULL, 
    "progress" integer NOT NULL DEFAULT -1, 
    "retries" integer NOT NULL DEFAULT 0,  
    PRIMARY KEY ("id_asset", "id_action", "settings")
);"""

]