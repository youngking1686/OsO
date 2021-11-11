from urllib.request import HTTPDefaultErrorHandler
from ks_api_client import ks_api
import pandas as pd
import datetime as dt
import NFO_expiry_calc, config
from nsetools import Nse
from db_query import Database
from tkinter import messagebox
nse = Nse()

db = Database('appni.db')
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
        
    def Pos_MIS_Market(self, ins_token, side, qty, tag):
        try:
            resp = self.client.place_order(order_type = "MIS", instrument_token = ins_token, transaction_type = side, quantity = qty, price = 0, tag = tag)
            return resp
        except Exception as e:
            messagebox.showerror("Error", "Exception when calling OrderApi->place_order: %s\n" % e)
            return
    
    def Pos_MIS_Limit(self, ins_token, side, qty, price, tag):
        try:
            resp = self.client.place_order(order_type = "MIS", instrument_token = ins_token, transaction_type = side, quantity = qty, price = price, tag = tag)
            return resp
        except Exception as e:
            messagebox.showerror("Error", "Exception when calling OrderApi->place_order: %s\n" % e)
            return
            
    def Exit_Market(self, ins_token, tag):
        try:
            resp = self.client.positions(position_type = "TODAYS")
            positions = resp['Success']
            quant = [position['netTrdQtyLot'] for position in positions if abs(position['netTrdQtyLot']) > 0 \
                and position['deliveryStatus'] == 12 and position['instrumentToken']]
            if quant:
                side = 'SELL' if quant[0] > 0 else 'BUY'
                response = self.client.place_order(order_type = "MIS", instrument_token = ins_token, transaction_type = side, quantity = quant[0], price = 0, tag = tag)
                return response
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
            elif positions and trade_type == 'long':
                longs = [position['instrumentToken'] for position in positions if position['netTrdQtyLot'] > 0 and position['deliveryStatus'] == 12]
                return True if ins_token in longs else False
            elif positions and trade_type == 'short':
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
            return resp
        except:
            return None
      
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
                        time = order['orderTimestamp'].split(' ')[3]
                        order_id = order['orderId']
                        name = order['instrumentName'] + '-' + str(order['expiryDate']) + '-' + str(order['strikePrice']) + '-' + str(order['optionType'])
                        side = order['transactionType']
                        qnty = order['orderQuantity']
                        status = order['status']
                        if status == 'TRAD':
                            price = next(trade['price'] for trade in trades if (trade['orderId']==order_id and trade['transactionType']==side))
                        else:
                            price = None
                        lis.append((i, order_id, time, name, side, price, qnty, status))
                    continue
                order_list = sorted(lis, key = lambda x: x[0], reverse=True)
                return order_list
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
        
    def long_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a):
        if ltp >= entry_price and a <= max_try and not exists:
            if limit:
                KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, entry_price,'Buy order')
            else:
                KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, 'Buy order')
            a+=1
        elif ltp <= stop_price and a <= max_try and exists:
            a+=1
            if limit:
                KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, stop_price,'Sell order')
            else:
                KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, 'Sell order')
        elif a > max_try:
            db.update_trade(opt, False)
        return a
    
    def short_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a):
        if ltp <= entry_price and a <= max_try and not exists:
            if limit:
                KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, entry_price,'Sell order')
            else:
                KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, 'Sell order')
            a+=1
        elif ltp >= stop_price and a <= max_try and exists:
            a+=1
            if limit:
                KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, stop_price,'Buy order')
            else:
                KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, 'Buy order')
        elif a > max_try:
            db.update_trade(opt, False)
        return a
    
    def trader(self, opt, ins_token, side, ltp, entry_price, stop_price, qty, max_try, a ,exists, spot_level, limit):
        limit = limit if not spot_level else False
        if not spot_level or (spot_level and (opt == 'NIFTY_CE' or opt == 'BANKNIFTY_CE')):
            if side == 'long':
                a = KS_ops.long_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a)
            elif side == 'short':
                a = KS_ops.short_action(self, opt, ins_token, ltp, entry_price, stop_price, max_try, exists, qty, limit, a)
        elif spot_level and (opt == 'NIFTY_PE' or opt == 'BANKNIFTY_PE'):
            if side == 'long':
                if ltp <= entry_price and a < max_try and not exists:
                    if limit:
                        KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, entry_price,'Buy order')
                    else:
                        KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, 'Buy order')
                    a+=1
                elif ltp >= stop_price and a < max_try and exists:
                    a+=1
                    if limit:
                        KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, stop_price,'Sell order')
                    else:
                        KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, 'Sell order')
                elif a >= max_try:
                    db.update_trade(opt, False)
                
            elif side == 'short':
                if ltp >= entry_price and a < max_try and not exists:
                    if limit:
                        KS_ops.Pos_MIS_Limit(self, ins_token, 'SELL', qty, entry_price,'Sell order')
                    else:
                        KS_ops.Pos_MIS_Market(self, ins_token, 'SELL', qty, 'Sell order')
                    a+=1
                elif ltp <= stop_price and a < max_try and exists:
                    a+=1
                    if limit:
                        KS_ops.Pos_MIS_Limit(self, ins_token, 'BUY', qty, stop_price,'Buy order')
                    else:
                        KS_ops.Pos_MIS_Market(self, ins_token, 'BUY', qty, 'Buy order')
                elif a >= max_try:
                    db.update_trade(opt, False)
        return a

def make_strikes():
    try:
        NIFTY = int(50 * round(nse.get_index_quote('Nifty 50')['lastPrice']/50))
        BANKNIFTY = int(100 * round(nse.get_index_quote('Nifty Bank')['lastPrice']/100))
        n_upstks = [('NIFTY', NIFTY+x*50) for x in range(10)]
        n_dwnstks = [('NIFTY', NIFTY-x*50) for x in range(10)]
        n_stks = sorted(set([*n_upstks, *n_dwnstks]))
        n_stk_list = list(zip(*n_stks))[1]
        bn_upstks = [('BANKNIFTY', BANKNIFTY+x*100) for x in range(10)]
        bn_dwnstks = [('BANKNIFTY', BANKNIFTY-x*100) for x in range(10)]
        bn_stks = sorted(set([*bn_upstks, *bn_dwnstks]))
        bn_stk_list = list(zip(*bn_stks))[1]
        return [*n_stks, *bn_stks], n_stk_list, bn_stk_list
    except:
        return None, None, None

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
        
def get_exh_token(symbols): #Ins_strike_optyp
    df = pd.read_csv('{}/temp/ins_toks.csv'.format(mainfolder), index_col=None)
    tokens=[]
    for symbol in symbols:
        symb = symbol.split('_')
        ins, opt_type, strike, expiry = symb[0], symb[1], int(symb[2]), symb[3]
        if expiry == 'current':
            dt = NFO_expiry_calc.getNearestWeeklyExpiryDate().strftime("%d%b%y").upper()
        elif expiry == 'next':
            dt = NFO_expiry_calc.getNextWeeklyExpiryDate().strftime("%d%b%y").upper()
        row = df.loc[(df.instrumentName==ins) & (df.expiry==dt) & (df.strike==strike) & (df.optionType==opt_type) & (df.exchange=='NSE')]
        tokens.append( (int(row['exchangeToken']), int(row['instrumentToken'])) )
    return tokens

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