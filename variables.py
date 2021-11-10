import tkinter as tk
from db_query import Database

# db=Database('appni.db')

username = tk.StringVar()
password = tk.StringVar()
app_id = tk.StringVar()
consumer_key = tk.StringVar()
access_token = tk.StringVar()

nft_lvl=tk.IntVar()
bnf_lvl=tk.IntVar()

n_ce_side=tk.StringVar()
n_ce_strk_var=tk.IntVar()
n_ce_entry=tk.StringVar()
n_ce_stop=tk.StringVar()
n_ce_max_try=tk.IntVar()
n_ce_qnty=tk.IntVar()
n_ce_spot_level=tk.IntVar()
n_ce_active=tk.IntVar()

n_pe_side=tk.StringVar()
n_pe_strk_var=tk.IntVar()
n_pe_entry=tk.StringVar()
n_pe_stop=tk.StringVar()
n_pe_max_try=tk.IntVar()
n_pe_qnty=tk.IntVar()
n_pe_spot_level=tk.IntVar()
n_pe_active=tk.IntVar()

bn_ce_active=tk.IntVar()
bn_ce_side=tk.StringVar()
bn_ce_strk_var=tk.IntVar()
bn_ce_entry=tk.StringVar()
bn_ce_stop=tk.StringVar()
bn_ce_max_try=tk.IntVar()
bn_ce_qnty=tk.IntVar()
bn_ce_spot_level=tk.IntVar()
bn_ce_active=tk.IntVar()

bn_pe_side=tk.StringVar()
bn_pe_strk_var=tk.IntVar()
bn_pe_entry=tk.StringVar()
bn_pe_stop=tk.StringVar()
bn_pe_max_try=tk.IntVar()
bn_pe_qnty=tk.IntVar()
bn_pe_spot_level=tk.IntVar()
bn_pe_active=tk.IntVar()

# def set_userdetails_var():
#     username.set(db.fetch_user()[1])
#     password.set(db.fetch_user()[2])
#     app_id.set(db.fetch_user()[3])
#     consumer_key.set(db.fetch_user()[4])
#     access_token.set(db.fetch_user()[5])

# def set_spo_var():
#     nft_lvl.set(db.fetch('NIFTY_CE')[8])
#     bnf_lvl.set(db.fetch('BANKNIFTY_CE')[8])

# def set_n_ce_var():
#     n_ce = db.fetch('NIFTY_CE')
#     n_ce_side.set(n_ce[2])
#     n_ce_strk_var.set(n_ce[3])
#     n_ce_entry.set(n_ce[4])
#     n_ce_stop.set(n_ce[5])
#     n_ce_max_try.set(n_ce[6])
#     n_ce_qnty.set(n_ce[7])
#     n_ce_spot_level.set(n_ce[8])
#     n_ce_active.set(n_ce[9])

# def set_n_pe_var():
#     n_pe = db.fetch('NIFTY_PE')
#     n_pe_side.set(n_pe[2])
#     n_pe_strk_var.set(n_pe[3])
#     n_pe_entry.set(n_pe[4])
#     n_pe_stop.set(n_pe[5])
#     n_pe_max_try.set(n_pe[6])
#     n_pe_qnty.set(n_pe[7])
#     n_pe_spot_level.set(n_pe[8])
#     n_pe_active.set(n_pe[9])

# def set_bn_ce_var():
#     bn_ce = db.fetch('BANKNIFTY_CE')
#     bn_ce_side.set(bn_ce[2])
#     bn_ce_strk_var.set(bn_ce[3])
#     bn_ce_entry.set(bn_ce[4])
#     bn_ce_stop.set(bn_ce[5])
#     bn_ce_max_try.set(bn_ce[6])
#     bn_ce_qnty.set(bn_ce[7])
#     bn_ce_spot_level.set(bn_ce[8])
#     bn_ce_active.set(bn_ce[9])

# def set_bn_pe_var():
#     bn_pe = db.fetch('BANKNIFTY_PE')
#     bn_pe_side.set(bn_pe[2])
#     bn_pe_strk_var.set(bn_pe[3])
#     bn_pe_entry.set(bn_pe[4])
#     bn_pe_stop.set(bn_pe[5])
#     bn_pe_max_try.set(bn_pe[6])
#     bn_pe_qnty.set(bn_pe[7])
#     bn_pe_spot_level.set(bn_pe[8])
#     bn_pe_active.set(bn_pe[9])