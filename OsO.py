from alice_blue import *
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.scrolledtext as scrolledtext
from ttkthemes import ThemedStyle
from tkinter.constants import CENTER, NORMAL, TRUE
import asynctkinter as at
import NFO_expiry_calc, config
from db_query import Database
from functools import partial
import operations as ops
from prettytable import PrettyTable
import mibian, datetime, sys

at.patch_unbind()
socket_opened = False
db = Database('appni.db')
ks = None
mainfolder = config.mainfolder
start_trading = False
live_positions, live_orders=[], []
n_ce_ltp, n_pe_ltp, bn_ce_ltp, bn_pe_ltp, nifty_ltp, bnknifty_ltp = 0, 0, 0, 0, 0, 0
n_ce_iv, n_pe_iv, bn_ce_iv, bn_pe_iv = 0, 0, 0, 0
n_ce_tok, n_pe_tok, bn_ce_tok, bn_pe_tok, nf_tok, bn_tok = 0, 0, 0, 0, 0, 0
n_ce_tried, n_pe_tried, bn_ce_tried, bn_pe_tried = 0, 0, 0, 0
days_to_expiry = 0

def start_websocket(NFO_LIST):
    global nf_tok
    global bn_tok
    global days_to_expiry
    username = '245632'
    password = 'Alib@890'
    api_secret = 're4kOfrybl8UXS3XPB3zWGbhL1rEsdw2rEydFME353BVuDdkArzeMoDji4iLo5cz' #ilay-account
    app_id = 'KoemGSfEvi'
    twoFA = '1987'
    excng = ['NSE', 'NFO']
    access_token = AliceBlue.login_and_get_access_token(username=username, password=password,\
            twoFA=twoFA,  api_secret=api_secret, app_id=app_id)
    alice = AliceBlue(username=username, password='something', access_token=access_token, \
            master_contracts_to_download=excng)

    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                            socket_open_callback=open_callback,
                            run_in_background=True)

    while(socket_opened==False):
        pass
    nifty50 = alice.get_instrument_by_symbol('NSE', 'Nifty 50')
    nf_tok = nifty50.token
    banknifty = alice.get_instrument_by_symbol('NSE', 'Nifty Bank')
    bn_tok = banknifty.token
    sub_list =[nifty50, banknifty]
    #Nifty  50 token 26000, #Bnifty token 26009
    expiry = NFO_expiry_calc.getNearestWeeklyExpiryDate()
    curr = datetime.date.today()
    days_to_expiry = (expiry - curr).days + 1
    for ins in NFO_LIST:
        sub_list.append(alice.get_instrument_for_fno(symbol=ins[0], expiry_date=expiry, is_fut=False, strike=ins[1], is_CE=False, exchange='NFO'))
        sub_list.append(alice.get_instrument_for_fno(symbol=ins[0], expiry_date=expiry, is_fut=False, strike=ins[1], is_CE=True, exchange='NFO'))
    alice.subscribe(sub_list, LiveFeedType.COMPACT)  

def event_handler_quote_update(message):
    global n_ce_ltp, n_pe_ltp, bn_ce_ltp, bn_pe_ltp, nifty_ltp, bnknifty_ltp, n_ce_iv, n_pe_iv, bn_ce_iv, bn_pe_iv
    ex_token = message['token']  #exchange token available from kotak ins_tok
    if ex_token == nf_tok:
        nifty_ltp = message['ltp']
    elif ex_token == bn_tok:
        bnknifty_ltp = message['ltp']
    elif ex_token == n_ce_tok:
        n_ce_ltp = message['ltp']
        n_ce_iv =  round(mibian.BS([nifty_ltp, n_ce_strike, 3.56, days_to_expiry], callPrice=n_ce_ltp).impliedVolatility, 2)
    elif ex_token == n_pe_tok:
        n_pe_ltp = message['ltp']
        n_pe_iv =  round(mibian.BS([nifty_ltp, n_pe_strike, 3.56, days_to_expiry], putPrice=n_pe_ltp).impliedVolatility, 2)
    elif ex_token == bn_ce_tok:
        bn_ce_ltp = message['ltp']
        bn_ce_iv =  round(mibian.BS([bnknifty_ltp, bn_ce_strike, 3.56, days_to_expiry], callPrice=bn_ce_ltp).impliedVolatility, 2)
    elif ex_token == bn_pe_tok:
        bn_pe_ltp = message['ltp']
        bn_pe_iv =  round(mibian.BS([bnknifty_ltp, bn_pe_strike, 3.56, days_to_expiry], putPrice=bn_pe_ltp).impliedVolatility, 2)
    else:
        pass

def open_callback():
    global socket_opened
    socket_opened = True
    # print("Socket Opened")

outs = [(x[1]+'_'+str(x[3])+'_current', x[3]) for x in db.fetch_all()]
symbols = list(zip(*outs))[0]
n_ce_strike, n_pe_strike, bn_ce_strike, bn_pe_strike = [x for x in list(zip(*outs))[1]]
NFO_LIST, N_strikes, BN_strikes = ops.make_strikes()

root = tk.Tk()
root.minsize(900, 600)
root.title("OSO")
root.resizable(width=False, height=False)
root.configure(background='#2e2a2a')
style = ThemedStyle(root)
style.set_theme("black")#("adapta")
style.configure('Test.TLabel', background= '#DAFF78', foreground="black")
# create frame style
s = ttk.Style()
s.configure('new.TFrame', background='#DAFF78')
tabControl = ttk.Notebook(root)

texts = ('NIFTY CALL', 'NIFTY PUT', 'BANKNIFTY CALL', 'BANKNIFTY PUT')
sides = ('short', 'long')

if not NFO_LIST:
    messagebox.showerror("Error", "Check your internet connection")
    sys.exit()
start_websocket(NFO_LIST)

if not ops.get_token_data():
    messagebox.showwarning("Warning", "Error downloading tokens")

import variables as v
class Set_Var:
    def userdetails_var():
        userr = db.fetch_user()
        v.username.set(userr[1])
        v.password.set(userr[2])
        v.app_id.set(userr[3])
        v.consumer_key.set(userr[4])
        v.access_token.set(userr[5])

    def spo_var():
        v.nft_lvl.set(db.fetch('NIFTY_CE')[8])
        v.bnf_lvl.set(db.fetch('BANKNIFTY_CE')[8])

    def n_ce_var():
        n_ce = db.fetch('NIFTY_CE')
        v.n_ce_side.set(n_ce[2])
        v.n_ce_strk_var.set(n_ce[3])
        v.n_ce_entry.set(n_ce[4])
        v.n_ce_stop.set(n_ce[5])
        v.n_ce_max_try.set(n_ce[6])
        v.n_ce_qnty.set(n_ce[7])
        v.n_ce_spot_level.set(n_ce[8])
        v.n_ce_active.set(n_ce[9])

    def n_pe_var():
        n_pe = db.fetch('NIFTY_PE')
        v.n_pe_side.set(n_pe[2])
        v.n_pe_strk_var.set(n_pe[3])
        v.n_pe_entry.set(n_pe[4])
        v.n_pe_stop.set(n_pe[5])
        v.n_pe_max_try.set(n_pe[6])
        v.n_pe_qnty.set(n_pe[7])
        v.n_pe_spot_level.set(n_pe[8])
        v.n_pe_active.set(n_pe[9])

    def bn_ce_var():
        bn_ce = db.fetch('BANKNIFTY_CE')
        v.bn_ce_side.set(bn_ce[2])
        v.bn_ce_strk_var.set(bn_ce[3])
        v.bn_ce_entry.set(bn_ce[4])
        v.bn_ce_stop.set(bn_ce[5])
        v.bn_ce_max_try.set(bn_ce[6])
        v.bn_ce_qnty.set(bn_ce[7])
        v.bn_ce_spot_level.set(bn_ce[8])
        v.bn_ce_active.set(bn_ce[9])

    def bn_pe_var():
        bn_pe = db.fetch('BANKNIFTY_PE')
        v.bn_pe_side.set(bn_pe[2])
        v.bn_pe_strk_var.set(bn_pe[3])
        v.bn_pe_entry.set(bn_pe[4])
        v.bn_pe_stop.set(bn_pe[5])
        v.bn_pe_max_try.set(bn_pe[6])
        v.bn_pe_qnty.set(bn_pe[7])
        v.bn_pe_spot_level.set(bn_pe[8])
        v.bn_pe_active.set(bn_pe[9])

Set_Var.userdetails_var()
Set_Var.spo_var()
Set_Var.n_ce_var()
Set_Var.n_pe_var()
Set_Var.bn_ce_var()
Set_Var.bn_pe_var()

access_code = tk.StringVar()
access_code.set('')
limit = tk.BooleanVar()
limit.set(False)

class Action:
    def save_broker():
        if v.username.get() == "" or v.password.get()=="" or v.consumer_key.get()=="" or \
            v.access_token.get()=="":
            messagebox.showerror("Error in Input", "Required Fields cannot be empty")
            return
        else:
            db.update_user(v.username.get(), v.password.get(), v.app_id.get(), v.consumer_key.get(), v.access_token.get())
            messagebox.showinfo("Success", "Details saved")
            save_brk["state"] = 'disabled'
            edit_brk['state'] = 'normal'
            f1_brk["state"] = 'disabled'
            f2_brk["state"] = 'disabled'
            f3_brk["state"] = 'disabled'
            f4_brk["state"] = 'disabled'
            f5_brk["state"] = 'disabled'
            
    def save_form(option, side, strk_var, entry, stop, max_try, qnty, active, spot_level):
        global n_ce_tok, n_pe_tok, bn_ce_tok, bn_pe_tok, n_ce_strike, n_pe_strike, bn_ce_strike, bn_pe_strike, v
        opt = 'NIFTY_CE' if option=='NIFTY CALL' else 'NIFTY_PE' if option=='NIFTY PUT' else 'BANKNIFTY_CE' \
            if option=='BANKNIFTY CALL' else 'BANKNIFTY_PE'
        if side.get() == "" or strk_var.get()=="" or entry.get()=="" or stop.get()=="" or max_try.get()=="":# or qnty.get()=="":
            messagebox.showerror("Error in Input", "Required Fields cannot be empty")
            return
        else:
            if option=='NIFTY CALL':
                global n_ce_tried
                n_ce_tried=0
            elif option=='NIFTY PUT':
                global n_pe_tried
                n_pe_tried=0
            elif option=='BANKNIFTY CALL':
                global bn_ce_tried
                bn_ce_tried=0
            elif option=='BANKNIFTY PUT':
                global bn_pe_tried
                bn_pe_tried=0
            db.update_all_params(opt, side.get(), int(strk_var.get()), float(entry.get()), float(stop.get()), int(max_try.get()), 
                                    int(qnty.get()), spot_level.get(), active.get())
        outs = [(x[1]+'_'+str(x[3])+'_current', x[3]) for x in db.fetch_all()]
        symbols = list(zip(*outs))[0]
        n_ce_strike, n_pe_strike, bn_ce_strike, bn_pe_strike = [x for x in list(zip(*outs))[1]]
        n_ce_tok, n_pe_tok, bn_ce_tok, bn_pe_tok = ops.update_exks_tokens(symbols)
        import variables as v
    
    def reset_form(option):
        Set_Var.n_ce_var() if option=='NIFTY CALL' else Set_Var.n_pe_var() if option=='NIFTY PUT' else Set_Var.bn_ce_var() \
                if option=='BANKNIFTY CALL' else Set_Var.bn_pe_var()
        Set_Var.spo_var()
            
    def place_order(option, side, qnty, spot_level):
        opt = 'NIFTY_CE' if option=='NIFTY CALL' else 'NIFTY_PE' if option=='NIFTY PUT' else 'BANKNIFTY_CE' \
            if option=='BANKNIFTY CALL' else 'BANKNIFTY_PE'
        ins_token = db.fetch(opt)[-1]
        action = 'BUY' if side.get() == 'long' else 'SELL'
        quantity = qnty.get()
        try:
            ks.Pos_MIS_Market(ins_token, action, quantity, 'oso')
            spot = spot_level.get()
            if spot:
                entry = nifty_ltp if (opt=='NIFTY_CE' or opt=='NIFTY_PE') else bnknifty_ltp
                stop = entry - 15 if (opt=='NIFTY_CE' or opt=='BANKNIFTY_CE') and  action == 'BUY' else \
                        entry + 15 if (opt=='NIFTY_CE' or opt=='BANKNIFTY_CE') and  action == 'SELL' else \
                        entry + 15 if (opt=='NIFTY_PE' or opt=='BANKNIFTY_PE') and  action == 'BUY' else entry - 15
            else:
                entry  = n_ce_ltp if opt=='NIFTY_CE' else n_pe_ltp if opt=='NIFTY_PE' else bn_ce_ltp \
                if opt=='BANKNIFTY_CE' else bn_pe_ltp
                stop = (entry - 5 if entry > 5 else 0) if action == 'BUY' else (entry + 5)
            db.update_entry_params(opt, side.get(), entry, stop, True)
            Action.reset_form(option)
        except AttributeError:
            messagebox.showerror("Error", "Check your connection, relogin and try again!")

    def break_even(option, side, entry, spot_level, active):
        opt = 'NIFTY_CE' if option=='NIFTY CALL' else 'NIFTY_PE' if option=='NIFTY PUT' else 'BANKNIFTY_CE' \
            if option=='BANKNIFTY CALL' else 'BANKNIFTY_PE'
        spot = spot_level.get()
        action = side.get()
        prev_entry = float(entry.get())
        if spot:
            stop = prev_entry
            entry = prev_entry + 100 if (opt=='NIFTY_CE' or opt=='BANKNIFTY_CE') and  action == 'long' else \
                    prev_entry - 100 if (opt=='NIFTY_CE' or opt=='BANKNIFTY_CE') and  action == 'short' else \
                    prev_entry - 100 if (opt=='NIFTY_PE' or opt=='BANKNIFTY_PE') and  action == 'long' else prev_entry + 100
        else:
            stop = prev_entry
            entry = (prev_entry + 50) if action == 'long' else ((prev_entry - 50) if prev_entry > 50 else 1)
        db.update_entry_params(opt, action, entry, stop, active.get())
        Action.reset_form(option)
                
    def exit_order(option):
        option = 'NIFTY_CE' if option=='NIFTY CALL' else 'NIFTY_PE' if option=='NIFTY PUT' else 'BANKNIFTY_CE' \
            if option=='BANKNIFTY CALL' else 'BANKNIFTY_PE'
        ins_token = db.fetch(option)[-1]
        db.update_trade(option, False)
        try:
            ks.Exit_Market(ins_token, 'oso')
            Action.reset_form(option)
            if option == 'NIFTY_CE':
                l.n_ce_status['text'] = 'CLS'
                l.n_ce_status.configure(background='#ff7500')
            elif option == 'NIFTY_PE':
                l.n_pe_status['text'] = 'CLS'
                l.n_pe_status.configure(background='#ff7500')
            elif option == 'BANKNIFTY_CE':
                l.bn_ce_status['text'] = 'CLS'
                l.bn_ce_status.configure(background='#ff7500')
            else:
                l.bn_pe_status['text'] = 'CLS'
                l.bn_pe_status.configure(background='#ff7500')
        except AttributeError:
            messagebox.showerror("Error", "Check your connection, relogin and try again!")
            
    def get_param(option, side, spot_level):
        spot = spot_level.get()
        if spot:
            entry = nifty_ltp if (option=='NIFTY CALL' or option=='NIFTY PUT') else bnknifty_ltp
            stop = entry - 15 if (option=='NIFTY CALL' or option=='BANKNIFTY CALL') and  side.get() == 'long' else \
                    entry + 15 if (option=='NIFTY CALL' or option=='BANKNIFTY CALL') and  side.get() == 'short' else \
                    entry + 15 if (option=='NIFTY CALL' or option=='BANKNIFTY PUT') and  side.get() == 'long' else entry - 15
        else:
            entry  = n_ce_ltp if option=='NIFTY CALL' else n_pe_ltp if option=='NIFTY PUT' else bn_ce_ltp \
            if option=='BANKNIFTY CALL' else bn_pe_ltp
            stop = (entry - 5 if entry > 5 else 0) if side.get() == 'long' else (entry + 5)
        v.n_ce_entry.set(entry) if option=='NIFTY CALL' else v.n_pe_entry.set(entry) if option=='NIFTY PUT' else v.bn_ce_entry.set(entry) \
            if option=='BANKNIFTY CALL' else v.bn_pe_entry.set(entry)
        v.n_ce_stop.set(stop) if option=='NIFTY CALL' else v.n_pe_stop.set(stop) if option=='NIFTY PUT' else v.bn_ce_stop.set(stop) \
            if option=='BANKNIFTY CALL' else v.bn_pe_stop.set(stop)
            
    def ks_login():
        global ks, start_trading #, app_stat
        if access_code.get() == "":
            messagebox.showerror("Error in Input", "Access code and Secret cannot be empty")
            return
        else:
            ks = ops.KS_ops(access_code.get())
            resp = ks.login()
            if resp=='ok':
                start_trading = True
                # app_stat = 'Kotak:\nConnected'
                messagebox.showinfo("Success", "Kotak Login Success!")
                return
            else:
                messagebox.showerror("Error", "Kotak Login Failed!")
                return
        
    def ks_positions():
        global live_positions, live_orders
        try:
            live_positions = ks.get_position()
        except AttributeError:
            messagebox.showerror("Error", "Check your connection and try again!") 
        ttk.Label(tab3, text = 'Positions', font = ('calibre',10,'bold')).grid(row=2,column=1, padx=8, pady=5)
        txt1 = scrolledtext.ScrolledText(tab3, undo=True, wrap='word', height = 22, width = 60, bg="light blue")
        txt1['font'] = ('consolas', '10')
        txt1.grid(row=3,column = 1, padx=10, pady=8)
        x=PrettyTable()
        x.field_names = ('Name', 'Quantity', 'Realized P&L')
        for position in live_positions:
            x.add_row(position)
        txt1.insert(tk.INSERT,x)

    def ks_orders():
        global live_orders
        try:
            live_orders = ks.get_orders()
        except AttributeError:
            messagebox.showerror("Error", "Check your connection and try again!")
        ttk.Label(tab4, text = 'Orders', font = ('calibre',10,'bold')).grid(row=2,column=1, padx=8, pady=5)
        txt2 = scrolledtext.ScrolledText(tab4, undo=True, wrap='word', height = 22, width = 95, bg="light green")
        txt2['font'] = ('consolas', '10')
        txt2.grid(row=3,column = 1, padx=10, pady=8)
        y=PrettyTable()
        y.field_names = ('Time', 'Name', 'Transaction', 'Quantity', 'Status')
        
        for order in live_orders:
            y.add_row(order)
        txt2.insert(tk.INSERT,y)
            
    def switch_brk():
        global save_brk, edit_brk, f1_brk, f2_brk, f3_brk, f4_brk, f5_brk
        save_brk["state"] = 'normal'
        edit_brk['state'] = 'disabled'
        f1_brk["state"] = 'normal'
        f2_brk["state"] = 'normal'
        f3_brk["state"] = 'normal'
        f4_brk["state"] = 'normal'
        f5_brk["state"] = 'normal'
    
    def enable_limit():
        val = limit.get()
        limit.set(val)

class gui_contents():
    def tabs():
        tabControl.add(tab1, text ='Kotak Connect')
        tabControl.add(tab2, text ='Trade Action')
        tabControl.add(tab3, text ='Positions')
        tabControl.add(tab4, text ='Orders')
        tabControl.pack(expand = 1, fill ="both", padx = 20)
        
    def trade_frame(frame, style, active, option, side, strk_var, entry, stop, max_try, qnty, spot_level):
        ttk.Label(frame, text = 'Strk', font = ('calibre',10,'bold'), style= style).grid(row=1,column=3, padx=3, pady=3)
        ttk.Label(frame, text = 'Qnty', font = ('calibre',10,'bold'), style= style).grid(row=2,column=3, padx=3, pady=3)
        ttk.Label(frame, text = 'Entry', font = ('calibre',10,'bold'), style= style).grid(row=1,column=5, padx=3, pady=3)
        ttk.Label(frame, text = 'Stop', font = ('calibre',10,'bold'), style= style).grid(row=2,column=5, padx=3, pady=3)
        ttk.Label(frame, text = 'Mx.Try', font = ('calibre',10,'bold'), style= style).grid(row=1,column=7, padx=3, pady=3)
        ttk.Label(frame, text = 'Tried', font = ('calibre',10,'bold'), style= style).grid(row=2,column=7, padx=3, pady=3)
        ttk.Label(frame, text = 'LTP', font = ('calibre',10,'bold'), style= style).grid(row=1,column=12, padx=3, pady=3)
        ttk.Label(frame, text = 'IV', font = ('calibre',10,'bold'), style= style).grid(row=2,column=12, padx=3, pady=3)
        
        ttk.Checkbutton(frame, variable = active, onvalue = 1, offvalue = 0, state='enabled').grid(row=1, column=1, padx=8, pady=3)
        ttk.Label(frame, text = option, width=17, font=('calibre',10, 'bold'), style= style).grid(row=1,column=2, padx=8, pady=3)
        ttk.Spinbox(frame, values=sides, textvariable=side, width=8, foreground="black").grid(row=2,column=2, padx=3, pady=3)
        strikes = N_strikes if option=='NIFTY CALL' or option=='NIFTY PUT' else BN_strikes
        ttk.Spinbox(frame, values=strikes, textvariable=strk_var, width=10, foreground="black").grid(row=1,column=4, padx=3, pady=3)
        lot_size = 50 if option=='NIFTY CALL' or option=='NIFTY PUT' else 25
        ttk.Spinbox(frame, from_=0, to=5000, increment=lot_size, textvariable=qnty, width=5, foreground="black").grid(row=2, column=4, padx=3, pady=3)
        ttk.Spinbox(frame, from_=0, to=100000, increment=0.5, textvariable=entry, width=10, foreground="black").grid(row=1, column=6, padx=3, pady=3)
        ttk.Spinbox(frame, from_=0, to=100000, increment=0.5, textvariable=stop, width=10, foreground="black").grid(row=2, column=6, padx=3, pady=3)
        ttk.Spinbox(frame, from_=0, to=100, increment=1, textvariable=max_try, width=5, foreground="black").grid(row=1, column=8, padx=3, pady=3)
        
        update_param = partial(Action.save_form, option, side, strk_var, entry, stop, max_try, qnty, active, spot_level)
        reset_param = partial(Action.reset_form, option)
        breakeven = partial(Action.break_even, option, side, entry, spot_level, active)
        enter_param = partial(Action.place_order, option, side, qnty, spot_level)
        exit_param = partial(Action.exit_order, option)
        get_param = partial(Action.get_param, option, side, spot_level)
        get_p = tk.Button(frame,text = 'G',  font = ('',12,'bold'), command = get_param, width=3, bg="#e6e600", state=NORMAL)
        get_p.grid(row=1,column=9, padx=6, pady=3)
        reset = tk.Button(frame,text = 'R',  font = ('',12,'bold'), command = reset_param, width=3, bg="#66d9ff", state=NORMAL)
        reset.grid(row=2,column=9, padx=6, pady=3)
        brk_eve = tk.Button(frame,text = 'B', font = ('',12,'bold'), command = breakeven, width=3, bg="#0066ff", state=NORMAL)
        brk_eve.grid(row=1,column=10, padx=6, pady=3)
        update = tk.Button(frame,text = 'U', font = ('',12,'bold'), command = update_param, width=3, state=NORMAL)
        update.grid(row=2, column=10, padx=6, pady=3)
        enter = tk.Button(frame,text = 'E', font = ('',12,'bold'), command = enter_param, width=3, bg="#33cc33")
        enter.grid(row=1,column=11, padx=6, pady=3)
        exit = tk.Button(frame,text = 'X', font = ('',12,'bold'), command = exit_param, width=3, bg="#ff3300")
        exit.grid(row=2,column=11, padx=6, pady=3)
        
    def connection():
        global save_brk, edit_brk, f1_brk, f2_brk, f3_brk, f4_brk, f5_brk
        ttk.Label(tab1, text = 'Username *', font=('calibre',10, 'bold')).grid(row=1,column=1, padx=10, pady=15)
        f1_brk = ttk.Entry(tab1,textvariable = v.username, font=('calibre',10,'normal'), state='disabled')
        f1_brk.grid(row=1,column=2, padx=3, pady=15)
        ttk.Label(tab1, text = 'Password *', font = ('calibre',10,'bold')).grid(row=1,column=3, padx=10, pady=10)
        f2_brk = ttk.Entry(tab1, textvariable = v.password, font = ('calibre',10,'normal'), show = '*', state='disabled')
        f2_brk.grid(row=1,column=4, padx=3, pady=10)
        ttk.Label(tab1, text = 'Access Code *', font = ('calibre',10,'bold')).grid(row=1,column=5, padx=10, pady=10)
        ttk.Entry(tab1, textvariable = access_code, font = ('calibre',10,'normal'), state='enabled').grid(row=1,column=6, padx=10, pady=10)
        ttk.Label(tab1, text = 'API APP id *', font = ('calibre',10,'bold')).grid(row=2,column=1, padx=10, pady=10)
        f3_brk = ttk.Entry(tab1, textvariable = v.app_id, font = ('calibre',10,'normal'), state='disabled')
        f3_brk.grid(row=2,column=2, padx=3, pady=10)
        ttk.Label(tab1, text = 'Consumer Key *', font = ('calibre',10,'bold')).grid(row=2,column=3, padx=10, pady=10)
        f4_brk = ttk.Entry(tab1, textvariable = v.consumer_key, font = ('calibre',10,'normal'), show = '*', state='disabled')
        f4_brk.grid(row=2,column=4, padx=3, pady=10)
        ttk.Label(tab1, text = 'Access Token *', font = ('calibre',10,'bold')).grid(row=3,column=1, padx=10, pady=10)
        f5_brk = ttk.Entry(tab1, textvariable = v.access_token, width=95, font = ('calibre',10,'normal'), show = '*', state='disabled')
        f5_brk.grid(row=3,column=2, columnspan=6, padx=3, pady=10)
        edit_brk = ttk.Button(tab1,text = 'Edit', command = Action.switch_brk, width=15, style='TButton')
        edit_brk.grid(row=4,column=1, padx=10, pady=10)
        save_brk = ttk.Button(tab1,text = 'Save', command = Action.save_broker, width=15, state='disabled')
        save_brk.grid(row=4,column=2, padx=10, pady=10)
        conn_brk = ttk.Button(tab1,text = 'Connect', command = Action.ks_login, width=15, state='enabled')
        conn_brk.grid(row=4,column=6, padx=10, pady=10)
    
    def trades():
        gui_contents.trade_frame(frame0, 'Test.TLabel', v.n_ce_active, texts[0], v.n_ce_side, v.n_ce_strk_var, v.n_ce_entry, v.n_ce_stop, v.n_ce_max_try, v.n_ce_qnty, v.nft_lvl)
        gui_contents.trade_frame(frame1, None, v.n_pe_active,  texts[1],v.n_pe_side, v.n_pe_strk_var, v.n_pe_entry, v.n_pe_stop, v.n_pe_max_try, v.n_pe_qnty, v.nft_lvl)
        gui_contents.trade_frame(frame2, 'Test.TLabel', v.bn_ce_active,  texts[2],v.bn_ce_side, v.bn_ce_strk_var, v.bn_ce_entry, v.bn_ce_stop, v.bn_ce_max_try, v.bn_ce_qnty, v.bnf_lvl)
        gui_contents.trade_frame(frame3, None, v.bn_pe_active,  texts[3],v.bn_pe_side, v.bn_pe_strk_var, v.bn_pe_entry, v.bn_pe_stop, v.bn_pe_max_try, v.bn_pe_qnty, v.bnf_lvl)
        
    def positions():
        pos_but = ttk.Button(tab3,text = 'Refresh', command = Action.ks_positions, width=15, state='enabled')
        pos_but.grid(row=1,column=1, padx=10, pady=10)
        
    def orders():
        ord_but = ttk.Button(tab4,text = 'Refresh', command = Action.ks_orders, width=15, state='enabled')
        ord_but.grid(row=1,column=1, padx=10, pady=10)
        
    def tab_contents():
        gui_contents.connection()
        gui_contents.trades()
        gui_contents.positions()
        gui_contents.orders()
 
tab1 = ttk.Frame(tabControl)
tab2 = ttk.Frame(tabControl)
tab3 = ttk.Frame(tabControl)
tab4 = ttk.Frame(tabControl)
mframe = ttk.Frame(root, width=800, height=200)
mframe.pack()
frame0 = ttk.Frame(tab2, width=800, height=300, style='new.TFrame')
frame0.pack(padx=10, pady=15)
frame1 = ttk.Frame(tab2, width=800, height=300)
frame1.pack(padx=10, pady=15)
frame2 = ttk.Frame(tab2, width=800, height=300, style='new.TFrame')
frame2.pack(padx=10, pady=15)
frame3 = ttk.Frame(tab2, width=800, height=300)
frame3.pack(padx=10, pady=15)
gui_contents.tabs()
gui_contents.tab_contents()

async def ltp_display(nf_ltp, bnf_ltp, opt0_ltp, opt1_ltp, opt2_ltp, opt3_ltp, opt0_tried, opt1_tried,
                      opt2_tried, opt3_tried, opt0_iv, opt1_iv, opt2_iv, opt3_iv):
    while True:
        n_ce_iv, n_pe_iv, bn_ce_iv, bn_pe_iv
        nf_ltp['text'] = f'NIFTY:  {nifty_ltp}'
        bnf_ltp['text'] = f'BANKNIFTY:  {bnknifty_ltp}'
        opt0_ltp['text'] = n_ce_ltp
        opt0_tried['text'] = n_ce_tried
        opt0_iv['text'] = n_ce_iv
        opt1_ltp['text'] = n_pe_ltp
        opt1_tried['text'] = n_pe_tried
        opt1_iv['text'] = n_pe_iv
        opt2_ltp['text'] = bn_ce_ltp
        opt2_tried['text'] = bn_ce_tried
        opt2_iv['text'] = bn_ce_iv
        opt3_ltp['text'] = bn_pe_ltp
        opt3_tried['text'] = bn_pe_tried
        opt3_iv['text'] = bn_pe_iv
        await at.sleep(800, after=opt3_tried.after)
        
async def ks_trader(n_ce_status, n_pe_status, bn_ce_status, bn_pe_status):
    while True:
        if start_trading:
            try:
                options = db.fetch_all()
                limit_order = limit.get()
                for option in options:
                    id, opt, side, strike, entry, stop, max_try, qnty, \
                        spot_level, trade, ex_token, ks_token = [val for val in option]
                    if trade:
                        exists = ks.check_position(ks_token, side)
                    else:
                        continue
                    if exists == 'glitch':
                        continue
                    else:
                        if opt=='NIFTY_CE':
                            global n_ce_tried
                            ltp = nifty_ltp if spot_level else n_ce_ltp 
                            n_ce_status['text'] = 'OPN' if exists else 'CLS'
                            n_ce_status.configure(background='#00ff00') if exists else n_ce_status.configure(background='#ff7500')
                            n_ce_tried = ks.trader(opt, ks_token, side, ltp, entry, stop, qnty, max_try, n_ce_tried, exists, spot_level, limit_order)
                        elif opt=='NIFTY_PE':
                            global n_pe_tried
                            ltp =  nifty_ltp if spot_level else n_pe_ltp
                            n_pe_status['text'] = 'OPN' if exists else 'CLS'
                            n_pe_status.configure(background='#00ff00') if exists else n_pe_status.configure(background='#ff7500')
                            n_pe_tried = ks.trader(opt, ks_token, side, ltp, entry, stop, qnty, max_try, n_pe_tried, exists, spot_level, limit_order)
                        elif opt=='BANKNIFTY_CE':
                            global bn_ce_tried
                            ltp =  bnknifty_ltp if spot_level else bn_ce_ltp
                            bn_ce_status['text'] = 'OPN' if exists else 'CLS'
                            bn_ce_status.configure(background='#00ff00') if exists else bn_ce_status.configure(background='#ff7500')
                            bn_ce_tried = ks.trader(opt, ks_token, side, ltp, entry, stop, qnty, max_try, bn_ce_tried, exists, spot_level, limit_order)
                        elif opt=='BANKNIFTY_PE':
                            global bn_pe_tried
                            ltp = bnknifty_ltp if spot_level else bn_ce_ltp
                            bn_pe_status['text'] = 'OPN' if exists else 'CLS'
                            bn_pe_status.configure(background='#00ff00') if exists else bn_pe_status.configure(background='#ff7500')
                            bn_pe_tried = ks.trader(opt, ks_token, side, ltp, entry, stop, qnty, max_try, bn_pe_tried, exists, spot_level, limit_order)     
                        continue
            except AttributeError:
                pass
        await at.sleep(1000, after=bn_pe_status.after)

ttk.Checkbutton(mframe, variable = v.nft_lvl, onvalue = 1, offvalue = 0, state='enabled').grid(row=3, column=1)
ttk.Label(mframe, text = 'Trade Nifty Level', font = ('calibre',10,'bold')).grid(row=2,column=1, padx=8, pady=15)

ttk.Checkbutton(mframe, variable = v.bnf_lvl,onvalue = 1, offvalue = 0, state='enabled').grid(row=3, column=2)
ttk.Label(mframe, text = 'Trade BankNifty Level', font = ('calibre',10,'bold')).grid(row=2,column=2, padx=8, pady=15)

ttk.Checkbutton(mframe, variable = limit, command = Action.enable_limit, onvalue = 1, offvalue = 0, state='enabled').grid(row=3, column=3, columnspan=6)
ttk.Label(mframe, text = 'Limit Orders', font = ('calibre',10,'bold')).grid(row=2,column=3, columnspan=6, padx=8, pady=15)

class labels:
    nf_ltp = ttk.Label(mframe, width=20, font=('calibre', 20))
    nf_ltp.grid(row = 1,column = 1, padx = 25, pady = 10)
    bnf_ltp = ttk.Label(mframe, width=20, font=('calibre', 20))
    bnf_ltp.grid(row = 1,column = 6, padx = 25, pady = 10)
    opt0_ltp = ttk.Label(frame0, width=10, font = ('calibre',10,'bold'), style= 'Test.TLabel', justify=CENTER)
    opt0_ltp.grid(row=1, column=13, padx=5, pady=10)
    opt1_ltp = ttk.Label(frame1, width=10, font = ('calibre',10,'bold'), justify=CENTER)
    opt1_ltp.grid(row=1, column=13, padx=5, pady=10)
    opt2_ltp = ttk.Label(frame2, width=10, font = ('calibre',10,'bold'), style= 'Test.TLabel', justify=CENTER)
    opt2_ltp.grid(row=1, column=13, padx=5, pady=10)
    opt3_ltp = ttk.Label(frame3, width=10, font = ('calibre',10,'bold'), justify=CENTER)
    opt3_ltp.grid(row=1, column=13, padx=5, pady=10)

    opt0_iv = ttk.Label(frame0, width=10, font = ('calibre',10,'bold'), style= 'Test.TLabel', justify=CENTER)
    opt0_iv.grid(row=2, column=13, padx=5, pady=10)
    opt1_iv = ttk.Label(frame1, width=10, font = ('calibre',10,'bold'), justify=CENTER)
    opt1_iv.grid(row=2, column=13, padx=5, pady=10)
    opt2_iv = ttk.Label(frame2, width=10, font = ('calibre',10,'bold'), style= 'Test.TLabel', justify=CENTER)
    opt2_iv.grid(row=2, column=13, padx=5, pady=10)
    opt3_iv = ttk.Label(frame3, width=10, font = ('calibre',10,'bold'), justify=CENTER)
    opt3_iv.grid(row=2, column=13, padx=5, pady=10)

    opt0_tried = ttk.Label(frame0, width=5, font = ('calibre',10,'bold'), style= 'Test.TLabel', justify=CENTER)
    opt0_tried.grid(row=2, column=8, padx=5, pady=10)
    opt1_tried = ttk.Label(frame1, width=5, font = ('calibre',10,'bold'), justify=CENTER)
    opt1_tried.grid(row=2, column=8, padx=5, pady=10)
    opt2_tried = ttk.Label(frame2, width=5, font = ('calibre',10,'bold'), style= 'Test.TLabel', justify=CENTER)
    opt2_tried.grid(row=2, column=8, padx=5, pady=10)
    opt3_tried = ttk.Label(frame3, width=5, font = ('calibre',10,'bold'), justify=CENTER)
    opt3_tried.grid(row=2, column=8, padx=5, pady=10)

    n_ce_status = ttk.Label(frame0, font = ('calibre',10,'bold'), width=5, style= 'Test.TLabel')
    n_ce_status.grid(row=2,column=1, padx=8, pady=5)
    n_pe_status = ttk.Label(frame1, font = ('calibre',10,'bold'), width=5)
    n_pe_status.grid(row=2,column=1, padx=8, pady=5)
    bn_ce_status = ttk.Label(frame2, font = ('calibre',10,'bold'), width=5, style= 'Test.TLabel')
    bn_ce_status.grid(row=2,column=1, padx=8, pady=5)
    bn_pe_status = ttk.Label(frame3, font = ('calibre',10,'bold'), width=5)
    bn_pe_status.grid(row=2,column=1, padx=8, pady=5)

l = labels()
at.start(ltp_display(l.nf_ltp, l.bnf_ltp, l.opt0_ltp, l.opt1_ltp, l.opt2_ltp, l.opt3_ltp,
                     l.opt0_tried, l.opt1_tried, l.opt2_tried, l.opt3_tried, l.opt0_iv, l.opt1_iv, l.opt2_iv, l.opt3_iv))
at.start(ks_trader(l.n_ce_status, l.n_pe_status, l.bn_ce_status, l.bn_pe_status))
root.mainloop()