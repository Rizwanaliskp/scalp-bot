#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   BINANCE FUTURES SCALPING BOT  —  v3.0                      ║
║   Strategy: Buy on dip | TP on pump | Fully configurable     ║
╚══════════════════════════════════════════════════════════════╝
"""

import time, logging
from datetime import datetime
from typing import Dict, List, Optional

# ════════════════════════════════════════════════════════════════
#  ⚙️  ALL SETTINGS  —  Edit anything here before running
# ════════════════════════════════════════════════════════════════
CFG = {

    # ── API Keys (for LIVE mode only) ──────────────────────────
    "api_key":    "XEyrUNtaCljqV5HIpGu99Hsaqwc5XRiqKUNEvptifYWwLeEFYq8xA5vvwL9GaS50",
    "api_secret": "8cPF7TobmlSBbScHWuBVPQktsRewHQDKty8a1bmEINik8BV36nWsWea67fDVXLHi",
    "use_testnet": False,

    # ── Pairs & Direction ───────────────────────────────────────
    "active_pairs": ["BTCUSDT"],    # BTCUSDT / ETHUSDT / BNBUSDT
    "direction":    "LONG",         # LONG only

    # ── Pre-place limits ────────────────────────────────────────
    "pre_place": 5,                 # how many buy limits to place at once

    # ── Max entries ─────────────────────────────────────────────
    "max_entries": 20,

    # ── Leverage ────────────────────────────────────────────────
    "leverage": 1,

    # ── Mode ────────────────────────────────────────────────────
    "test_mode":    False,
    "paper_balance": 1000.0,

    # ════════════════════════════════════════════════════════════
    #  💰 AMOUNT PER ENTRY
    #  amount_mode = "percent"  →  uses amount_pct (% of balance)
    #  amount_mode = "dollar"   →  uses amount_usd (fixed $ amount)
    # ════════════════════════════════════════════════════════════
    "amount_mode": "percent",   # ← change to "dollar" for fixed $
    "amount_pct":   5.0,        # e.g. 5.0 = 5% of balance per entry
    "amount_usd":  50.0,        # e.g. 50 = $50 per entry (fixed)

    # ════════════════════════════════════════════════════════════
    #  📉 DIP % — how much price must drop before buying
    #
    #  dip_mode = "same"    →  all entries use dip_pct
    #  dip_mode = "custom"  →  each entry uses its own % from dip_levels
    # ════════════════════════════════════════════════════════════
    "dip_mode": "same",         # ← change to "custom" for per-entry dips
    "dip_pct":   1.0,           # used when dip_mode = "same"

    # Per-entry dip % (used when dip_mode = "custom")
    # Each number = how much to drop from the PREVIOUS level
    # Example: [1.0, 1.5, 2.0] → entry1 at -1%, entry2 at -1.5% from entry1, etc.
    "dip_levels": [
        1.0,   # entry #1
        1.0,   # entry #2
        1.5,   # entry #3
        1.5,   # entry #4
        2.0,   # entry #5
        2.0,   # entry #6
        1.0,   # entry #7
        1.0,   # entry #8
        1.5,   # entry #9
        1.5,   # entry #10
        2.0,   # entry #11
        2.0,   # entry #12
        1.0,   # entry #13
        1.0,   # entry #14
        1.5,   # entry #15
        1.5,   # entry #16
        2.0,   # entry #17
        2.0,   # entry #18
        1.0,   # entry #19
        1.0,   # entry #20
    ],

    # ════════════════════════════════════════════════════════════
    #  📈 TP % — how much price must pump to take profit
    #
    #  tp_mode = "same"    →  all entries use tp_pct
    #  tp_mode = "custom"  →  each entry uses its own % from tp_levels
    # ════════════════════════════════════════════════════════════
    "tp_mode": "same",          # ← change to "custom" for per-entry TPs
    "tp_pct":   0.30,           # used when tp_mode = "same"

    # Per-entry TP % (used when tp_mode = "custom")
    "tp_levels": [
        0.30,  # entry #1
        0.30,  # entry #2
        0.40,  # entry #3
        0.40,  # entry #4
        0.50,  # entry #5
        0.50,  # entry #6
        0.30,  # entry #7
        0.30,  # entry #8
        0.40,  # entry #9
        0.40,  # entry #10
        0.50,  # entry #11
        0.50,  # entry #12
        0.30,  # entry #13
        0.30,  # entry #14
        0.40,  # entry #15
        0.40,  # entry #16
        0.50,  # entry #17
        0.50,  # entry #18
        0.30,  # entry #19
        0.30,  # entry #20
    ],

    # TP trigger: activates the TP limit order (keep at half of tp_pct)
    # Formula: trigger = entry_price * (1 + tp_trigger_pct/100)
    "tp_trigger_pct": 0.15,    # halfway point — TP order gets activated here
}


# ════════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scalp_bot.log", mode="a"),
    ],
)
log = logging.getLogger("ScalpBot")


# ════════════════════════════════════════════════════════════════
#  CONFIG DISPLAY  —  shows all settings clearly at startup
# ════════════════════════════════════════════════════════════════
def show_config(cfg: dict, start_price: float = 0, symbol: str = ""):
    print(f"\n{'═'*62}")
    print(f"  ⚙️  SETTINGS SUMMARY  {symbol}")
    print(f"{'═'*62}")

    # Amount
    if cfg["amount_mode"] == "percent":
        print(f"  💰 Amount per entry  : {cfg['amount_pct']}% of balance")
        if start_price:
            bal = cfg.get("paper_balance", 1000)
            amt = bal * cfg["amount_pct"] / 100
            print(f"                         ≈ ${amt:.2f} per entry")
    else:
        print(f"  💰 Amount per entry  : ${cfg['amount_usd']:.2f} fixed")

    # Dip
    if cfg["dip_mode"] == "same":
        print(f"  📉 Buy dip           : {cfg['dip_pct']}% (same for all entries)")
    else:
        print(f"  📉 Buy dip           : CUSTOM per entry")

    # TP
    if cfg["tp_mode"] == "same":
        print(f"  📈 Take profit       : {cfg['tp_pct']}% (same for all entries)")
    else:
        print(f"  📈 Take profit       : CUSTOM per entry")

    print(f"  🔢 Max entries       : {cfg['max_entries']}")
    print(f"  📦 Pre-place limits  : {cfg['pre_place']}")

    # Show entry-by-entry table if start price known
    if start_price:
        print(f"\n  {'Entry':<7} {'Dip%':>6} {'Buy @':>12} {'Trig @':>12} {'TP @':>12} {'TP%':>6}")
        print(f"  {'-'*57}")
        p = start_price
        for i in range(1, min(cfg["pre_place"] + 3, cfg["max_entries"] + 1)):
            dip   = _get_dip(cfg, i)
            tp    = _get_tp(cfg, i)
            trig_pct = cfg["tp_trigger_pct"]
            p     = round(p * (1 - dip / 100), 2)
            trig  = round(p * (1 + trig_pct / 100), 2)
            tp_p  = round(p * (1 + tp / 100), 2)
            marker = " ← pre-placed" if i <= cfg["pre_place"] else ""
            print(f"  #{i:<6} {dip:>5.1f}%  {p:>12,.2f} {trig:>12,.2f} {tp_p:>12,.2f}  {tp:>5.2f}%{marker}")
        if cfg["max_entries"] > cfg["pre_place"] + 3:
            print(f"  ... (continues to entry #{cfg['max_entries']})")

    print(f"{'═'*62}\n")


# ════════════════════════════════════════════════════════════════
#  CONFIG HELPERS
# ════════════════════════════════════════════════════════════════
def _get_dip(cfg: dict, level_idx: int) -> float:
    """Get dip % for level N (1-indexed)."""
    if cfg["dip_mode"] == "custom":
        levels = cfg["dip_levels"]
        return levels[min(level_idx - 1, len(levels) - 1)]
    return cfg["dip_pct"]


def _get_tp(cfg: dict, entry_num: int) -> float:
    """Get TP % for entry N (1-indexed)."""
    if cfg["tp_mode"] == "custom":
        levels = cfg["tp_levels"]
        return levels[min(entry_num - 1, len(levels) - 1)]
    return cfg["tp_pct"]


def _get_amount(cfg: dict, balance: float) -> float:
    """Get USDT amount for one entry."""
    if cfg["amount_mode"] == "dollar":
        return cfg["amount_usd"]
    return balance * (cfg["amount_pct"] / 100)


# ════════════════════════════════════════════════════════════════
#  PAPER TRADING ENGINE
# ════════════════════════════════════════════════════════════════
class PaperTrader:
    def __init__(self, balance: float):
        self.balance         = balance
        self.initial_balance = balance
        self._orders: Dict[str, dict] = {}
        self._positions: Dict[str, dict] = {}
        self._oid = 1
        self.trades: List[dict] = []

    def _new_id(self) -> str:
        oid = f"P{self._oid:05d}"
        self._oid += 1
        return oid

    def _pos(self, symbol: str) -> dict:
        return self._positions.setdefault(symbol, {"size": 0.0, "avg": 0.0})

    def get_balance(self) -> float:
        return self.balance

    def place_limit_buy(self, symbol: str, qty: float, price: float) -> dict:
        oid = self._new_id()
        o = {"id": oid, "symbol": symbol, "side": "BUY", "type": "LIMIT",
             "qty": qty, "price": price, "trigger": None,
             "status": "NEW", "fill_price": None}
        self._orders[oid] = o
        log.info(f"  📋 BUY  LIMIT  {qty:.5f} {symbol} @ {price:,.2f}  [#{oid}]")
        return o

    def place_tp(self, symbol: str, qty: float,
                 trigger: float, limit: float, entry_price: float = 0.0) -> dict:
        oid = self._new_id()
        o = {"id": oid, "symbol": symbol, "side": "SELL", "type": "TAKE_PROFIT",
             "qty": qty, "price": limit, "trigger": trigger,
             "entry_price": entry_price,
             "status": "NEW", "fill_price": None, "reduce_only": True}
        self._orders[oid] = o
        log.info(f"  📋 SELL TP     {qty:.5f} {symbol}"
                 f"  trigger@{trigger:,.2f} → limit@{limit:,.2f}  [#{oid}]")
        return o

    def cancel(self, order_id: str) -> bool:
        o = self._orders.get(order_id)
        if o and o["status"] == "NEW":
            o["status"] = "CANCELED"
            log.info(f"  ✖  Canceled [#{order_id}]")
            return True
        return False

    def process_tick(self, symbol: str, price: float) -> List[dict]:
        filled: List[dict] = []
        for o in list(self._orders.values()):
            if o["symbol"] != symbol or o["status"] != "NEW":
                continue
            hit = False
            fp  = o["price"]
            if o["type"] == "LIMIT" and o["side"] == "BUY":
                if price <= o["price"]:
                    hit, fp = True, o["price"]
            elif o["type"] == "TAKE_PROFIT" and o["side"] == "SELL":
                if price >= o["price"]:
                    hit, fp = True, o["price"]
            if hit:
                o["status"] = "FILLED"
                o["fill_price"] = fp
                self._apply(o, fp)
                filled.append(dict(o))
        return filled

    def _apply(self, o: dict, fp: float):
        sym, qty = o["symbol"], o["qty"]
        pos = self._pos(sym)
        if o["side"] == "BUY":
            cost = qty * fp
            self.balance -= cost
            new_size   = pos["size"] + qty
            pos["avg"] = (pos["size"] * pos["avg"] + cost) / new_size
            pos["size"] = new_size
            log.info(f"  ✅ FILLED BUY  {qty:.5f} {sym} @ {fp:,.2f}"
                     f"  │ pos={pos['size']:.5f}  bal=${self.balance:.2f}")
        elif o["side"] == "SELL" and o.get("reduce_only"):
            qty = min(qty, pos["size"])
            if qty <= 0: return
            entry_p = o.get("entry_price") or pos["avg"]
            pnl = qty * (fp - entry_p)
            self.balance += qty * fp
            pos["size"] = max(0.0, pos["size"] - qty)
            self.trades.append({"sym": sym, "qty": qty, "entry": round(entry_p, 2),
                                 "exit": fp, "pnl": pnl,
                                 "time": datetime.now().strftime("%H:%M:%S")})
            log.info(f"  💰 FILLED SELL {qty:.5f} {sym} @ {fp:,.2f}"
                     f"  │ pnl=${pnl:+.4f}  bal=${self.balance:.2f}")

    def print_summary(self):
        total_pnl = sum(t["pnl"] for t in self.trades)
        wins = sum(1 for t in self.trades if t["pnl"] > 0)
        print(f"\n{'═'*60}")
        print(f"  📊  PAPER TRADING SUMMARY")
        print(f"{'═'*60}")
        print(f"  Start  : ${self.initial_balance:.2f}")
        print(f"  End    : ${self.balance:.2f}")
        print(f"  PnL    : ${total_pnl:+.4f}")
        print(f"  Trades : {len(self.trades)}  (wins: {wins})")
        print(f"{'─'*60}")
        for t in self.trades[-10:]:
            e = "🟢" if t["pnl"] > 0 else "🔴"
            print(f"  {e} {t['time']}  {t['sym']}"
                  f"  qty={t['qty']:.5f}"
                  f"  entry={t['entry']:,.2f}  exit={t['exit']:,.2f}"
                  f"  pnl=${t['pnl']:+.4f}")
        print(f"{'═'*60}\n")


# ════════════════════════════════════════════════════════════════
#  STRATEGY
# ════════════════════════════════════════════════════════════════
PRICE_PREC = {"BTCUSDT": 1, "ETHUSDT": 2, "BNBUSDT": 2}
QTY_PREC   = {"BTCUSDT": 5, "ETHUSDT": 4, "BNBUSDT": 3}


class Strategy:
    def __init__(self, symbol: str, trader: PaperTrader, cfg: dict):
        self.sym    = symbol
        self.trader = trader
        self.cfg    = cfg
        self.pp     = PRICE_PREC.get(symbol, 2)
        self.qp     = QTY_PREC.get(symbol, 4)

        self.entries: List[dict]      = []
        self.pending_buys: List[dict] = []   # {id, price, level_idx}
        self.level_idx        = 0    # next level index to place
        self.n_entries        = 0    # entries taken this cycle
        self.n_tps            = 0    # total TPs hit
        self.first_entry_from = 0.0  # starting reference price
        self.running          = False

    def rp(self, v): return round(v, self.pp)
    def rq(self, v): return round(v, self.qp)

    def _dip(self) -> float:
        """Dip % for the NEXT level to be placed."""
        return _get_dip(self.cfg, self.level_idx + 1)

    def _tp(self, entry_num: int) -> float:
        return _get_tp(self.cfg, entry_num)

    def _amount(self, price: float) -> float:
        return _get_amount(self.cfg, self.trader.get_balance())

    def _active_pending(self) -> List[dict]:
        return [pb for pb in self.pending_buys
                if self.trader._orders.get(pb["id"], {}).get("status") == "NEW"]

    def _lowest_pending_price(self) -> float:
        active = self._active_pending()
        return min((pb["price"] for pb in active), default=0.0)

    # ── start ──
    def start(self, price: float):
        self.running          = True
        self.first_entry_from = price
        log.info(f"\n{'═'*60}")
        log.info(f"  🚀 {self.sym}  started @ {price:,.2f}")
        log.info(f"{'═'*60}")
        show_config(self.cfg, price, self.sym)
        self._place_initial_buys(price)

    def on_tick(self, price: float):
        if not self.running: return
        for o in self.trader.process_tick(self.sym, price):
            if o["side"] == "BUY":
                self._on_buy(o)
            elif o["side"] == "SELL":
                self._on_tp(o)

    def status(self):
        active = self._active_pending()
        log.info(f"\n  [{self.sym}] entries={self.n_entries}"
                 f"  open={len(self.entries)}"
                 f"  pending={len(active)}"
                 f"  TPs={self.n_tps}")
        for e in self.entries:
            log.info(f"    Entry #{e['n']}: {e['qty']:.5f} @ {e['price']:,.2f}"
                     f"  TP→{e['tp_price']:,.2f}  (+{e['tp_pct']}%)")
        for pb in active:
            log.info(f"    Pending buy @ {pb['price']:,.2f}  (level #{pb['level_idx']+1})")

    # ── place initial 5 buy limits ──
    def _place_initial_buys(self, from_price: float):
        self.pending_buys = []
        self.level_idx    = 0
        p     = from_price
        count = min(self.cfg["pre_place"], self.cfg["max_entries"])
        log.info(f"  [{self.sym}] Placing {count} buy limits:")
        for _ in range(count):
            dip   = _get_dip(self.cfg, self.level_idx + 1)
            p     = self.rp(p * (1 - dip / 100))
            amt   = _get_amount(self.cfg, self.trader.get_balance())
            qty   = self.rq(amt / p)
            if qty <= 0: break
            order = self.trader.place_limit_buy(self.sym, qty, p)
            self.pending_buys.append({
                "id": order["id"], "price": p, "level_idx": self.level_idx
            })
            self.level_idx += 1
        log.info(f"  [{self.sym}] ✅ {len(self.pending_buys)} limits placed"
                 f"  │ lowest @ {self.pending_buys[-1]['price']:,.2f}")

    # ── add one more buy below lowest pending ──
    def _add_one_buy(self):
        total = self.n_entries + len(self._active_pending())
        if total >= self.cfg["max_entries"]:
            return
        lowest = self._lowest_pending_price()
        if lowest <= 0: return
        dip   = _get_dip(self.cfg, self.level_idx + 1)
        p     = self.rp(lowest * (1 - dip / 100))
        amt   = _get_amount(self.cfg, self.trader.get_balance())
        qty   = self.rq(amt / p)
        if qty <= 0: return
        order = self.trader.place_limit_buy(self.sym, qty, p)
        self.pending_buys.append({
            "id": order["id"], "price": p, "level_idx": self.level_idx
        })
        self.level_idx += 1
        log.info(f"  [{self.sym}] ➕ Added buy @ {p:,.2f}"
                 f"  (level #{self.level_idx}  dip {dip}%)")

    # ── buy filled ──
    def _on_buy(self, o: dict):
        fp, qty = o["fill_price"], o["qty"]
        self.n_entries += 1

        # Remove from pending list
        self.pending_buys = [pb for pb in self.pending_buys if pb["id"] != o["id"]]

        # TP for this entry using its specific tp%
        tp_pct   = self._tp(self.n_entries)
        trig_pct = self.cfg["tp_trigger_pct"]
        tp_lim   = self.rp(fp * (1 + tp_pct   / 100))
        tp_trig  = self.rp(fp * (1 + trig_pct / 100))
        tp_order = self.trader.place_tp(self.sym, qty, tp_trig, tp_lim,
                                        entry_price=fp)

        self.entries.append({
            "n":        self.n_entries,
            "price":    fp,
            "qty":      qty,
            "tp_id":    tp_order["id"] if tp_order else None,
            "tp_price": tp_lim,
            "tp_pct":   tp_pct,
        })

        log.info(f"  [{self.sym}] ► ENTRY #{self.n_entries}"
                 f"  qty={qty:.5f} @ {fp:,.2f}"
                 f"  TP @ {tp_lim:,.2f} (+{tp_pct}%)"
                 f"  │ pending: {len(self._active_pending())}")

        # Keep 5 limits ready
        self._add_one_buy()

    # ── TP filled ──
    def _on_tp(self, o: dict):
        fp, oid = o["fill_price"], o["id"]
        self.n_tps += 1
        orig_price = None

        for i, e in enumerate(self.entries):
            if e["tp_id"] == oid:
                orig_price = e["price"]
                log.info(f"  [{self.sym}] ◆ TP #{self.n_tps}"
                         f"  entry#{e['n']}  qty={e['qty']:.5f}"
                         f"  bought@{e['price']:,.2f} → sold@{fp:,.2f}"
                         f"  (+{e['tp_pct']}%)")
                self.entries.pop(i)
                break

        # All entries closed → reset cycle at same levels
        if not self.entries:
            log.info(f"  [{self.sym}] 🔄 Cycle done."
                     f"  Total entries: {self.n_entries}  TPs: {self.n_tps}")
            self.n_entries = 0

            # Cancel remaining pending buys
            for pb in self.pending_buys:
                self.trader.cancel(pb["id"])
            self.pending_buys = []

            # Restart 5 limits from same original reference
            log.info(f"  [{self.sym}] Restarting same levels from {self.first_entry_from:,.2f}...")
            self._place_initial_buys(self.first_entry_from)


# ════════════════════════════════════════════════════════════════
#  LIVE CLIENT (Binance API)
# ════════════════════════════════════════════════════════════════
class LiveClient:
    def __init__(self, api_key, api_secret, testnet=False):
        from binance.um_futures import UMFutures  # type: ignore
        if testnet:
            self.api = UMFutures(key=api_key, secret=api_secret,
                                 base_url="https://testnet.binancefuture.com")
        else:
            self.api = UMFutures(key=api_key, secret=api_secret)
        self.api.ping()
        log.info("✅ Binance Futures connected!")

    def get_balance(self):
        for a in self.api.account().get("assets", []):
            if a["asset"] == "USDT":
                return float(a["availableBalance"])
        return 0.0

    def get_price(self, symbol):
        return float(self.api.ticker_price(symbol=symbol)["price"])

    def set_leverage(self, symbol, lev):
        self.api.change_leverage(symbol=symbol, leverage=lev)

    def get_symbol_info(self, symbol):
        for s in self.api.exchange_info()["symbols"]:
            if s["symbol"] == symbol:
                return {"price_prec": s["pricePrecision"],
                        "qty_prec":   s["quantityPrecision"]}
        return {"price_prec": 2, "qty_prec": 3}

    def place_limit_buy(self, symbol, qty, price):
        return self.api.new_order(symbol=symbol, side="BUY", type="LIMIT",
                                  quantity=qty, price=price, timeInForce="GTC")

    def place_tp(self, symbol, qty, trigger, limit):
        return self.api.new_order(symbol=symbol, side="SELL", type="TAKE_PROFIT",
                                  quantity=qty, price=limit, stopPrice=trigger,
                                  timeInForce="GTC", reduceOnly=True)

    def cancel(self, symbol, order_id):
        try: self.api.cancel_order(symbol=symbol, orderId=order_id)
        except Exception as e: log.warning(f"Cancel: {e}")

    def check_order(self, symbol, order_id):
        try:
            o = self.api.query_order(symbol=symbol, orderId=order_id)
            return o if o.get("status") == "FILLED" else None
        except: return None


# ════════════════════════════════════════════════════════════════
#  BOT
# ════════════════════════════════════════════════════════════════
class ScalpBot:
    def __init__(self, cfg: dict):
        self.cfg   = cfg
        self.paper = PaperTrader(cfg["paper_balance"]) if cfg["test_mode"] else None
        self.live  = None
        self.strats: Dict[str, Strategy] = {}
        if not cfg["test_mode"]:
            self.live = LiveClient(cfg["api_key"], cfg["api_secret"], cfg["use_testnet"])

    def run_simulation(self, price_series: Dict[str, List[float]]):
        log.info("\n🧪 PAPER TRADING SIMULATION\n")
        for sym in self.cfg["active_pairs"]:
            if sym not in price_series: continue
            s = Strategy(sym, self.paper, self.cfg)
            s.start(price_series[sym][0])
            self.strats[sym] = s
        ticks = max(len(p) for p in price_series.values())
        for i in range(1, ticks):
            for sym, prices in price_series.items():
                if i < len(prices) and sym in self.strats:
                    self.strats[sym].on_tick(prices[i])
        for s in self.strats.values():
            s.status()
        self.paper.print_summary()

    def run_live(self):
        for sym in self.cfg["active_pairs"]:
            try: self.live.set_leverage(sym, self.cfg["leverage"])
            except Exception as e: log.warning(f"Leverage {sym}: {e}")
        for sym in self.cfg["active_pairs"]:
            price = self.live.get_price(sym)
            s = Strategy(sym, None, self.cfg)  # no paper trader in live
            s.trader = type('T', (), {  # minimal live adapter
                'get_balance': self.live.get_balance,
                '_orders': {},
                'place_limit_buy': lambda sy, q, p: self.live.place_limit_buy(sy, q, p),
                'place_tp': lambda sy, q, tr, lm, ep=0: self.live.place_tp(sy, q, tr, lm),
                'cancel': lambda oid: self.live.cancel(sym, oid),
                'process_tick': lambda sy, pr: [],
            })()
            s.start(price)
            self.strats[sym] = s
        log.info(f"\n🚀 Live running | {self.cfg['active_pairs']} | Ctrl+C to stop\n")
        try:
            while True:
                for sym in self.cfg["active_pairs"]:
                    try:
                        # Poll each pending buy and TP order
                        strat = self.strats[sym]
                        for pb in list(strat.pending_buys):
                            filled = self.live.check_order(sym, pb["id"])
                            if filled:
                                fp  = float(filled["avgPrice"])
                                qty = float(filled["executedQty"])
                                strat._on_buy({"fill_price": fp, "qty": qty, "id": pb["id"]})
                        for e in list(strat.entries):
                            if not e.get("tp_id"): continue
                            filled = self.live.check_order(sym, e["tp_id"])
                            if filled:
                                fp = float(filled["avgPrice"])
                                strat._on_tp({"fill_price": fp, "id": e["tp_id"]})
                    except Exception as ex:
                        log.error(f"Tick error {sym}: {ex}")
                time.sleep(2)
        except KeyboardInterrupt:
            log.info("\n⛔ Stopped")
            for s in self.strats.values(): s.status()


# ════════════════════════════════════════════════════════════════
#  TEST PRICE GENERATOR
# ════════════════════════════════════════════════════════════════
def make_test_prices(start=75000.0):
    prices = [start]
    p = start
    def step(p, chg, n):
        for _ in range(n):
            p = round(p * (1 + chg/100), 1)
            prices.append(p)
        return p
    p = step(p,  0.00,  5)
    p = step(p, -0.08, 14)
    p = step(p, -0.07, 10)
    p = step(p,  0.02,  4)
    p = step(p, -0.10, 14)
    p = step(p,  0.14, 20)
    p = step(p,  0.04,  8)
    p = step(p, -0.08, 13)
    p = step(p, -0.07, 10)
    p = step(p,  0.12, 18)
    p = step(p,  0.02,  8)
    return prices


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"

    if mode == "test":
        cfg = dict(CFG)
        cfg["test_mode"] = True
        bot    = ScalpBot(cfg)
        prices = make_test_prices(75000.0)
        log.info(f"Ticks: {len(prices)}  Range: {min(prices):,.2f} – {max(prices):,.2f}")
        bot.run_simulation({"BTCUSDT": prices})

    elif mode == "live":
        cfg = dict(CFG)
        cfg["test_mode"] = False
        ScalpBot(cfg).run_live()

    else:
        print("Usage: python scalp_bot.py [test|live]")
