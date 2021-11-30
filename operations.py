from urllib.request import HTTPDefaultErrorHandler
from ks_api_client import ks_api
import pandas as pd
import datetime as dt
import NFO_expiry_calc, config
from db_query import Database
from tkinter import messagebox
# from nsetools import Nse
from pynse import *
nse = Nse()

db = Database('app.db')
mainfolder = config.mainfolder
client = None

class KS_ops:
    def __init__(self, access_code):
        detail = db.fetch_user()
        user_id = detail[1]
        self.password = detail[2]
        app_id = detail[3]
        consumer_key = detail[4]
        access_token = detail[5]
        self.access_code = access_code
        self.client = ks_api.KSTradeApi(access_token = access_token, userid = user_id, \
                                consumer_key = consumer_key, ip = "127.0.0.1", \
                                app_id = app_id)
        
    def login(self):
        try:
            self.client.login(password = self.password)
            self.client.session_2fa(access_code = self.access_code)
            return "ok"
        except:
            return None
        
    def logout(self):
        try:
            self.client.logout()
            return "ok"
        except:
            return None
        
    def Pos_MIS_Market(self, ins_token, side, qty, tag):
        try:
            resp = self.client.place_order(order_type = "MIS", instrument_token = ins_token, transaction_type = side, quantity = qty, price = 0, tag = tag)
            return f"{tag} placed"
        except Exception as e:
            messagebox.showerror("Error", "Exception when calling OrderApi->place_order: %s\n" % e)
            return
    
    def Pos_MIS_Limit(self, ins_token, side, qty, price, tag):
        try:
            resp = self.client.place_order(order_type = "MIS", instrument_token = ins_token, transaction_type = side, quantity = qty, price = price, tag = tag)
            return f"{tag} placed"
        except Exception as e:
            messagebox.showerror("Error", "Exception when calling OrderApi->place_order: %s\n" % e)
            return
            
    def Exit_Market(self, ins_token, price, tag, limi):
        try:
            if not limi:
                price = 0
            resp = self.client.positions(position_type = "TODAYS")
            positions = resp['Success']
            quant = [position['netTrdQtyLot'] for position in positions if abs(position['netTrdQtyLot']) > 0 \
                and position['deliveryStatus'] == 12 and position['instrumentToken']]
            if quant:
                side = 'SELL' if quant[0] > 0 else 'BUY'
                response = self.client.place_order(order_type = "MIS", instrument_token = ins_token, transaction_type = side, quantity = quant[0], price = price, tag = tag)
                return f"{tag} placed"
            else:
                messagebox.showwarning("Error", "No Open position to Exit")
                return
        except Exception as e:
            messagebox.showerror("Error", "Exception when calling OrderApi->place_order: %s\n" % e)
            return

    def check_position(self, ins_token, trade_type):
        try:
            resp = self.client.positions(position_type = "TODAYS")
            positions = resp['Success']
            if not positions:
                return False
            elif positions and trade_type == 'buy':
                longs = [position['instrumentToken'] for position in positions if position['netTrdQtyLot'] > 0 and position['deliveryStatus'] == 12]
                return True if ins_token in longs else False
            elif positions and trade_type == 'sell':
                shorts = [position['instrumentToken'] for position in positions if position['netTrdQtyLot'] < 0 and position['deliveryStatus'] == 12]
                return True if ins_token in shorts else False
        except:
            return 'glitch'
        
    def get_position(self):
        try:
            positions = self.client.positions(position_type = "TODAYS")['Success']
            if not positions:
                return None
            resp = [(pos['instrumentName'], pos['netTrdQtyLot'], round(pos['realizedPL'],2), pos['grossUtilization']) for pos in positions if pos['deliveryStatus'] == 12]
            tpnl = sum([pos[2] for pos in resp])
            return resp, tpnl
        except:
            return None, None
      
    def get_orders(self):
        try:
            orders = self.client.order_report()['success']
            trades = self.client.trade_report()['success']
            if not orders:
                return None
            else:
                lis = []
                for i, order in enumerate(orders):
                    if order['product'] == 'MIS' :
                        tim = order['orderTimestamp'].split(' ')[3].split(':')[:-1]
                        time = ':'.join(tim)
                        order_id = order['orderId']
                        name = order['instrumentName'] + '-' + str(order['expiryDate']) + '-' + str(order['strikePrice']) + '-' + str(order['optionType'])
                        side = order['transactionType']
                        qnty = order['orderQuantity']
                        status = order['status']
                        if status == 'TRAD':
                            price = next(trade['price'] for trade in trades if (trade['orderId']==order_id and trade['transactionType']==side))
                        else:
                            price = next(str(order['price']) + '/ ' + str(order['triggerPrice']) for order in orders if (order['orderId']==order_id))
                        lis.append((i, order_id, time, name, side, price, qnty, status))
                    continue
                order_list = sorted(lis, key = lambda x: x[0], reverse=True)
                return order_list
        except:
            return None
        
    def get_open_orders(self):
        try:
            orders = self.client.order_report()['success']
            if not orders:
                return None
            else:
                list_of_opn = [order['orderId'] for order in orders if order['status'] == 'OPN']
                return list_of_opn
        except:
            return None
        
    def get_order_detail(self, order_id):
        try:
            orders = self.client.order_report()['success']
            if not orders:
                return None
            else:
                details = [(order['instrumentName'] + '-' + str(order['expiryDate']) + '-' + str(order['strikePrice']), order['transactionType'],\
                    order['orderQuantity'], order['price'], order['triggerPrice']) for order in orders if (order['orderId'] == order_id\
                            and (order['status'] != 'TRAD' or order['status'] != 'CAN'))]
                return details[0]
        except:
            return None
    
    def cancel_order(self, order_id):
        try:
            resp = self.client.cancel_order(order_id)
            messagebox.showinfo("Cancelled", f"Cancelled order: {order_id}")
            return resp
        except Exception as e:
            messagebox.showerror("Error", "Failed Cancelling order: %s\n" % e)
            return
    
    def cancel_all_order(self):
        try:
            orders = self.get_open_orders()
            if not orders:
                messagebox.showinfo("Warning", "No open orders to Cancel")
                return
            for order in orders:
                self.client.cancel_order(order)
            messagebox.showinfo("Cancelled", "Cancelled all open orders")
            return
        except Exception as e:
            messagebox.showerror("Error", "Failed Cancelling order: %s\n" % e)
            return
    
    def modify_order(self, order_id, qnty, price, trigger, win):
        try:
            resp = self.client.modify_order(order_id = order_id, quantity = int(qnty), price = float(price), disclosed_quantity = 0, trigger_price = float(trigger), validity = "GFD")
            messagebox.showinfo("Modified", f"Modified order: {order_id}")
            win.destroy()
            return resp
        except Exception as e:
            messagebox.showerror("Error", "Failed Modifying order: %s\n" % e)
            win.destroy()
            return
        
    def long_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a):
        res = None
        if ltp >= entry_price and a <= max_try and not exists:
            if limit:
                res = KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, entry_price,'Auto Buy limit order')
            else:
                res = KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, 'Auto Buy market order')
            a+=1
        elif ltp <= stop_price and a <= max_try and exists:
            a+=1
            if limit:
                res = KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, stop_price,'Auto Sell limit order')
            else:
                res = KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, 'Auto Sell market order')
        elif a > max_try:
            db.update_trade(opt, False)
        return a, res
    
    def short_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a):
        res = None
        if ltp <= entry_price and a <= max_try and not exists:
            if limit:
                res = KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, entry_price,'Auto Sell limit order')
            else:
                res = KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, 'Auto Sell market order')
            a+=1
        elif ltp >= stop_price and a <= max_try and exists:
            a+=1
            if limit:
                res =  KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, stop_price,'Auto Buy limit order')
            else:
                res = KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, 'Auto Buy market order')
        elif a > max_try:
            db.update_trade(opt, False)
        return a, res
    
    def trader(self, opt, ins_token, side, ltp, entry_price, stop_price, qty, max_try, a ,exists, spot_level, limit):
        limit = limit if not spot_level else False
        res = None
        if not spot_level or (spot_level and (opt == 'NIFTY_CE' or opt == 'BANKNIFTY_CE')):
            if side == 'buy':
                a, res = KS_ops.long_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a)
            elif side == 'sell':
                a, res = KS_ops.short_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a)
        elif spot_level and (opt == 'NIFTY_PE' or opt == 'BANKNIFTY_PE'):
            if side == 'buy':
                if ltp <= entry_price and a < max_try and not exists:
                    if limit:
                        res = KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, entry_price, f'{opt} Auto Buy limit order')
                    else:
                        res = KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, f'{opt} Auto Buy market order')
                    a+=1
                elif ltp >= stop_price and a < max_try and exists:
                    a+=1
                    if limit:
                        res = KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, stop_price, f'{opt} Auto Sell limit order')
                    else:
                        res = KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, f'{opt} Auto Sell market order')
                elif a >= max_try:
                    db.update_trade(opt, False)
                
            elif side == 'sell':
                if ltp >= entry_price and a < max_try and not exists:
                    if limit:
                        res = KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, entry_price, f'{opt} Auto Sell limit order')
                    else:
                        res = KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, f'{opt} Sell market order')
                    a+=1
                elif ltp <= stop_price and a < max_try and exists:
                    a+=1
                    if limit:
                        res = KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, stop_price, f'{opt} Auto Buy limit order')
                    else:
                        res = KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, f'{opt} Auto Buy market order')
                elif a >= max_try:
                    db.update_trade(opt, False)
        return a, res

def make_strikes():
    # try:
        # NIFTY = int(50 * round(nse.get_index_quote('Nifty 50')['lastPrice']/50))
        # BANKNIFTY = int(100 * round(nse.get_index_quote('Nifty Bank')['lastPrice']/100))
        NIFTY = int(50 * round(nse.get_indices(IndexSymbol.Nifty50)['last']/50)) #pynse
        BANKNIFTY = int(100 * round(nse.get_indices(IndexSymbol.NiftyBank)['last']/100)) #pynse
        n_upstks = [('NIFTY', NIFTY+x*50) for x in range(10)]
        n_dwnstks = [('NIFTY', NIFTY-x*50) for x in range(10)]
        n_stks = sorted(set([*n_upstks, *n_dwnstks]))
        n_stk_list = list(zip(*n_stks))[1]
        bn_upstks = [('BANKNIFTY', BANKNIFTY+x*100) for x in range(10)]
        bn_dwnstks = [('BANKNIFTY', BANKNIFTY-x*100) for x in range(10)]
        bn_stks = sorted(set([*bn_upstks, *bn_dwnstks]))
        bn_stk_list = list(zip(*bn_stks))[1]
        return [*n_stks, *bn_stks], n_stk_list, bn_stk_list
    # except:
    #     return None, None, None

def get_token_data():
    try:
        df_FnO = pd.DataFrame()
        symbol_file = '{}/temp/ins_toks.csv'.format(mainfolder)
        trd_date = dt.datetime.today().strftime("%d_%m_%Y")
        url = 'https://preferred.kotaksecurities.com/security/production/TradeApiInstruments_FNO_{}.txt'.format(trd_date)
        df_FnO = pd.read_csv(url, sep='|', index_col=None)
        nms = ['BANKNIFTY', 'NIFTY']
        df_FnO = df_FnO[df_FnO['instrumentName'].isin(nms)]
        df_FnO.reset_index(drop=True, inplace=True)
        df_FnO.to_csv(symbol_file)
        return True
    except:
        return False
        
def update_exks_tokens(symbols): #Ins_strike_optyp
    df = pd.read_csv('{}/temp/ins_toks.csv'.format(mainfolder), index_col=None)
    ex_tokens=[]
    for symbol in symbols:
        symb = symbol.split('_')
        ins, opt_type, strike, expiry = symb[0], symb[1], int(symb[2]), symb[3]
        if expiry == 'current':
            dt = NFO_expiry_calc.getNearestWeeklyExpiryDate().strftime("%d%b%y").upper()
        elif expiry == 'next':
            dt = NFO_expiry_calc.getNextWeeklyExpiryDate().strftime("%d%b%y").upper()
        try:
            row = df.loc[(df.instrumentName==ins) & (df.expiry==dt) & (df.strike==strike) & (df.optionType==opt_type) & (df.exchange=='NSE')]
            db.update_tokens(ins+'_'+opt_type, int(row['exchangeToken']), int(row['instrumentToken']))
            ex_tokens.append(int(row['exchangeToken']))
        except:
            db.update_tokens(ins+'_'+opt_type, 0, 0)
            ex_tokens.append(0)
            continue
    return [tok for tok in ex_tokens]

def get_oi_spurts(instrument):
    expiry = NFO_expiry_calc.getNearestWeeklyExpiryDate()
    df = nse.option_chain(instrument, expiry)
    df_ce = df[['strikePrice', 'CE.openInterest', 'CE.changeinOpenInterest', 'CE.pchangeinOpenInterest',
       'CE.totalTradedVolume', 'CE.impliedVolatility', 'CE.lastPrice', 'CE.change', 'CE.pChange']].copy()
    df_ce = df_ce.rename(columns=lambda x: x.replace('CE.', ''))
    df_ce['Opt'] = 'CE'
    df_pe = df[['strikePrice', 'PE.openInterest', 'PE.changeinOpenInterest', 'PE.pchangeinOpenInterest',
        'PE.totalTradedVolume', 'PE.impliedVolatility', 'PE.lastPrice', 'PE.change', 'PE.pChange']].copy()
    df_pe = df_pe.rename(columns=lambda x: x.replace('PE.', ''))
    df_pe['Opt'] = 'PE'
    df1 = pd.concat([df_ce, df_pe]).round(2)
    df1.drop(['changeinOpenInterest', 'totalTradedVolume', 'change'], axis = 1, inplace=True)
    df1.rename(columns={'strikePrice': 'Strike', 'openInterest': 'OI', 
                   'pchangeinOpenInterest':'%c OI', 'impliedVolatility':'IV', 'lastPrice':'LTP', 'pChange':'%c price'}, inplace=True)
    df1 = df1[['Strike', 'Opt', 'LTP', '%c price', 'OI', '%c OI', 'IV']]
    print(df1)
    #Long build up -> oi +ve, %c +ve
    df_lb = df1.loc[(df1['%c price'] > 0) & (df1['%c OI'] > 0)]
    lbu = df_lb.sort_values(by=['%c OI'], ascending=False).values.tolist()

    #Short build up -> oi +ve, %c -ve
    df_sb = df1.loc[(df1['%c price'] < 0) & (df1['%c OI'] > 0)]
    sbu = df_sb.sort_values(by=['%c OI'], ascending=False).values.tolist()
    
    #Long unwinding - oi -ve, %c -ve
    df_lu = df1.loc[(df1['%c price'] < 0) & (df1['%c OI'] > 0)]
    lu = df_lu.sort_values(by=['%c OI'], ascending=False).values.tolist()

    #Short Covering - oi -ve, %c +ve
    df_sc = df1.loc[(df1['%c price'] > 0) & (df1['%c OI'] < 0)]
    sc = df_sc.sort_values(by=['%c OI'], ascending=True).values.tolist()
    return lbu, sbu, lu, sc
    
    
    
    