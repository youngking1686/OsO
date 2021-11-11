import sqlite3
import os
import threading

lock = threading.Lock()

if not os.path.isfile('appni.db'):
    conn = sqlite3.connect('appni.db')
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS opt_data (
            id INTEGER PRIMARY KEY,
            option TEXT NOT NULL UNIQUE,
            side TEXT,
            strike INTEGER,
            entry REAL,
            stop REAL,
            max_try INTEGER,
            qnty INTEGER,
            spot_level BOOLEAN NOT NULL,
            trade BOOLEAN NOT NULL,
            ex_token INTEGER,
            ks_token INTEGER
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL UNIQUE,
            app_id TEXT NOT NULL UNIQUE,
            consumer_key TEXT NOT NULL UNIQUE,
            access_token TEXT NOT NULL UNIQUE
        )
    """)
    defaults = [('NIFTY_CE', '', 0, '', '', '', 50, 0, 0, 0, 0), ('NIFTY_PE', '', 0, '', '', '', 50, 0, 0, 0, 0),
           ('BANKNIFTY_CE', '',0, '', '', '', 25, 0, 0, 0, 0), ('BANKNIFTY_PE', '', 0, '', '', '', 25, 0, 0, 0, 0)]
    for default in defaults:
        cur.execute("""INSERT INTO opt_data (option, side, strike, entry, stop, max_try, 
                     qnty, spot_level, trade, ex_token, ks_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (default))
    cur.execute("""INSERT INTO account (username, password, app_id, consumer_key, 
                access_token) VALUES (?, ?, ?, ?, ?)""", ('username', 'password', 'xxxx', 'xxxx', 'xxxx'))
    conn.commit()
    
class Database:
    def __init__(self, db):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.conn.commit()

    def fetch_user(self):
        self.cur.execute("""SELECT * FROM account""")
        rows = self.cur.fetchall()
        return rows[0]        
    
    def update_user(self, username, password, app_id, consumer_key, access_token):
        self.cur.execute("""UPDATE account SET username = ?, password = ?, app_id = ?, consumer_key = ?, 
                access_token = ? WHERE id = ?""", (username, password, app_id, consumer_key, access_token, 1))
        self.conn.commit()
    
    def fetch(self, option):
        self.cur.execute("""SELECT * FROM opt_data WHERE option = ?""", (option,))
        rows = self.cur.fetchall()
        return rows[0]

    def fetch_all(self):
        self.cur.execute("""SELECT * FROM opt_data""")
        rows = self.cur.fetchall()
        return rows

    def update_all_params(self, option, side, strike, entry, stop, max_try, qnty, spot_level, trade):
        try:
            lock.acquire(True)
            opt = option.split('_')
            if opt[0] == 'NIFTY':
                Database.ref_lvl(self, 'NIFTY', spot_level)
            else:
                Database.ref_lvl(self, 'BANKNIFTY', spot_level)
            self.cur.execute("""UPDATE opt_data SET side = ?, strike = ?, entry = ?, stop = ?, max_try = ?, qnty = ?, trade = ? WHERE option = ?""", \
                (side, strike, entry, stop, max_try, qnty, trade, option))
            self.conn.commit()
        finally:
            lock.release()
    
    def update_entry_params(self, option, side, entry, stop, trade):
        try:
            lock.acquire(True)
            self.cur.execute("""UPDATE opt_data SET side = ?, entry = ?, stop = ?, trade = ? WHERE option = ?""", (side, entry, stop, trade, option))
            self.conn.commit()
        finally:
            lock.release()
        
    def update_trade(self, option, trade):
        self.cur.execute("""UPDATE opt_data SET trade = ? WHERE option = ?""", (trade, option))
        self.conn.commit()
        
    def update_tokens(self, option, ex_token, ks_token):
        self.cur.execute("""UPDATE opt_data SET ex_token = ?, ks_token = ? WHERE option = ?""", (ex_token, ks_token, option))
        self.conn.commit()
            
    def ref_lvl(self, instrument, spot_level):
        if instrument =='NIFTY':
            opts = ['NIFTY_CE', 'NIFTY_PE']
        else:
            opts = ['BANKNIFTY_CE', 'BANKNIFTY_PE']
        for option in opts:
            self.cur.execute("""UPDATE opt_data SET spot_level = ? WHERE option = ?""", (spot_level, option))
            continue
        self.conn.commit()
        
    def __del__(self):
        self.conn.close()