import sqlite3


DB_TEMPLATE = [
"CREATE TABLE articles (id_article INTEGER PRIMARY KEY ASC, source TEXT, guid TEXT, content TEXT);",
"CREATE TABLE history (id_channel INTEGER, tstamp INTEGER, id_article INTEGER);"
]




class NewsDB():
    def __init__(self, path):
        try:
            self.conn = sqlite3.connect(path) 
            self.cur = self.conn.cursor()
        except:
            raise (Exception, "Unable to connect database.")

    def __len__(self):
        return True

    def query(self, q, *args):
        self.cur.execute(q,*args)

    def fetchall(self):
        return self.cur.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
     
    def close(self):
        self.conn.close()

    def sanit(self, instr):
        try: 
            return str(instr).replace("''","'").replace("'","''").decode("utf-8")
        except: 
            return instr.replace("''","'").replace("'","''")
      
    def query(self, q, *args):
        self.cur.execute(q.replace("%s", "?"), *args)

    def lastid(self):
        r = self.cur.lastrowid
        return r




def create_db(path):
    news_db = NewsDB(path)
    for query in DB_TEMPLATE:
        news_db.query(query)
    news_db.commit()