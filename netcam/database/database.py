# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

# database class for the netcam application

import sqlite3
import os
from datetime import datetime, timedelta


class Database:
    """ sqlite3 database """

    DBFILE = 'database/netcam.db'

    def __init__(self):
        """ initialise the database """
        with sqlite3.connect(self.DBFILE) as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clips (
                    filename PRIMARY KEY, 
                    idx INTEGER NOT NULL, 
                    ymdhms TEXT NOT NULL, 
                    infos TEXT NOT NULL
                )
            """)
            # check for success
            res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clips';")
            if res is None:
                raise BaseException("Error: cannot build mandatory database 'netcam', table 'clips'!")
        pass

    # ----------
    def _get_time_frame(self, fromhr, tohr):
        """ get timestamps now-fromhr and now-tohr  """
        now = datetime.now()
        fromdt = now - timedelta(hours=fromhr)
        todt = now - timedelta(hours=tohr)
        return fromdt, todt

    # ----------
    def _get_rows(self, sql):
        """ get all rows for the sql statement """
        with sqlite3.connect(self.DBFILE) as con:
            cur = con.cursor()
            cur.execute(sql)
            return cur.fetchall()

    # ----------
    def get_clips_per_day(self):
        """ get the number of clips, by date, descending """
        sql = """
          SELECT ymd, COUNT(ymd) as clps
          FROM (SELECT SUBSTR(CAST(ymdhms AS varchar(14)),1,8) as 'ymd' FROM clips) as days
          GROUP BY ymd
          ORDER BY ymd DESC
        """
        return self._get_rows(sql)

    # ----------
    def get_clips_for_day(self, idx):
        """ get clip data for day 'idx' (yyyymmdd) """
        sql = """
        SELECT * FROM clips
        WHERE SUBSTR(CAST(ymdhms AS varchar(14)),1,8) = '?'
        ORDER BY ymdhms DESC
        """
        sql = sql.replace("?", idx)
        return self._get_rows(sql)

    # ----------
    def get_clips(self, fromhr, tohr):
        """ get the list of clips created between fromhr and tohr """
        fromdt, todt = self._get_time_frame(fromhr, tohr)
        fromdts = fromdt.strftime("%Y%m%d%H%M%S")
        todts = todt.strftime("%Y%m%d%H%M%S")
        # query database table clips
        with sqlite3.connect(self.DBFILE) as con:
            cur = con.cursor()
            sql = "SELECT * FROM clips WHERE ymdhms <= ? AND ymdhms >= ?"
            cur.execute(sql, (fromdts, todts))
            return cur.fetchall()

    def get_clips_last_hrs(self, hrs):
        """ get list of clips from the last 'hrs' hours """
        return self.get_clips(0,hrs)

    # ----------
    def set_clip(self, file, idx, ymdhms, infos):
        """ register clip in the database as soon as the file(clip) is closed
              filename: fully qualified filename and -path
              ymdhms: date and time the clip was created (yyyymmddhhmmss)
              infos: the clips attributes (dictionary)
        """
        with sqlite3.connect(self.DBFILE) as con:
            cur = con.cursor()
            # start transaction (implicit)
            sql = "INSERT INTO clips (filename, idx, ymdhms, infos) VALUES (?,?,?,?)"
            cur.execute(sql, (file, int(idx), ymdhms, str(infos)))
            con.commit() # close transaction
        pass

# ----------
if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')