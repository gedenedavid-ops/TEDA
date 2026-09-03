# TEDA — Slide Deck (10 slides · Hackathon lablab.ai × Alpaca)

> Use this content to build your slides on Canva.
> Each slide specifies which image/screenshot to capture.

---

## Slide 1 — Cover

**Title** : TEDA  
**Subtitle** : Options Alpha Agent — Smart Money Vision × Alpaca  
**Footer** : Hackathon lablab.ai × Alpaca · September 2026  

**Image** : TEDA logo (use a dark green/black gradient background with white text — terminal/trading style). Clean layout, no image needed.

---

## Slide 2 — The Problem

**Title** : Why an autonomous agent?

**Text** :
- The US options market is complex — too much noise for a single human
- Technical setups appear and disappear in minutes
- Discipline (risk management) is hard to maintain manually
- An agent never sleeps, never hesitates, never breaks the rules

**Image** : Screenshot of a busy SPY chart with lots of candles (shows market "noise"). Source: TradingView or Yahoo Finance.

---

## Slide 3 — What TEDA Does

**Title** : TEDA in 3 numbers

**Text** (3 columns):

| 🔭 | ⚡ | 🛡️ |
|---|---|---|
| **10 assets** | **5 minutes** | **5 filters** |
| monitored 24/7 | per analysis cycle | before every trade |

- Automatic scanning every 5 minutes
- Institutional order flow detection (Smart Money)
- Multi-leg options execution (debit spreads + iron condors)
- Automatic SL/TP exit

**Image** : None — keep it clean with the 3 metrics displayed large.

---

## Slide 4 — The SMV Strategy (5 Filters)

**Title** : The SMV Chain — 5 filters, zero compromise

**Text** (left-to-right or top-to-bottom flow):

```
① HTF Bias (D1)  →  ② OB Zone (H1)  →  ③ FVG (H1)  →  ④ Liquidity Swept  →  ⑤ Market Shift LTF  →  ✅ ENTRY
```

| Filter | Question | Rule |
|--------|----------|------|
| ① Bias | Trend? | HH+HL = bullish 80/20 |
| ② OB Zone | Where to act? | Unmitigated zone |
| ③ FVG | Confirmed? | Imbalance validates the zone |
| ④ Liquidity | Trap or safe? | Swept = clean, else inducement |
| ⑤ Shift LTF | Trigger? | BOS in bias direction |

**If 1 filter fails → NONE (no trade).**

**Image** : A simple flow diagram (arrows between 5 blocks), or the table above styled in Canva with green/red colors.

---

## Slide 5 — Options Strategies (B/B/B)

**Title** : 3 signals → 3 options strategies

**Text** :

```
🟢 BUY  →  Call Debit Spread
           (buy ATM call + sell OTM call)
           Defined risk, profit capped at spread width

🔴 SELL →  Put Debit Spread
           (buy ATM put + sell OTM put)
           Same structure, bearish direction

🟡 NEUTRAL →  Iron Condor
              (sell put spread + sell call spread)
              Range trading, credit collected
```

**Image** : Simplified P&L diagrams for each strategy:
- Call Debit Spread: curve rising after the long strike
- Put Debit Spread: curve rising below the long strike
- Iron Condor: "tent" curve with max profit in the center

Create these directly in Canva with simple shapes (no screenshot needed).

---

## Slide 6 — Risk Management

**Title** : Risk Gates — Discipline before profit

**Text** (3 blocks):

```
🔒 1% max per trade
   $1,000 on $100k equity
   Auto-calculated

📐 Minimum RR 1:7
   Trade rejected if ratio < 7
   Fallback TP built-in

🚪 Automatic exit
   SL = technical invalidation
   TP = liquidity target or 1:7
   Checked every cycle (5 min)
```

**Image** : Dashboard widget showing P&L with a small loss (-0.13% on the Sep 3 screenshot). Capture the equity widget from the TEDA dashboard.

---

## Slide 7 — Alpaca Infrastructure

**Title** : Alpaca Stack — 3 building blocks

**Text** (3 columns):

| 📡 Trading API | 🔌 MCP Server | ⌨️ CLI |
|---|---|---|
| IEX OHLCV data | AI connected to Alpaca | Terminal commands |
| MLEG options orders | Real-time positions | `python -m cli account` |
| Paper trading $100k | API debug without IDE | `python -m cli watchlist` |

+ **Featherless** : Open-source LLM (Llama 3.1 8B) for reasoning  
+ **Koyeb** : 24/7 deployment, auto-deploy from GitHub  
+ **Streamlit** : Interactive 4-tab dashboard

**Image** : Simple architecture diagram:
```
[Alpaca API] ←→ [TEDA Agent] ←→ [Featherless LLM]
                    ↓
              [Streamlit Dashboard] → [Koyeb 24/7]
```

Create this in Canva with boxes and arrows.

---

## Slide 8 — Live Dashboard

**Title** : 24/7 Monitoring

**Image** : **Full screenshot of the TEDA dashboard** (Streamlit screen with all 4 tabs visible, ideally the Watchlist tab with live signals).

Capture when the market is open for live data.

**Small text** at bottom: Streamlit Dashboard hosted on Koyeb — auto-refresh every 60s.

---

## Slide 9 — Live Results

**Title** : First trades — September 3, 2026

**Text** :

| Asset | Signal | Strategy | RR | Status |
|-------|--------|----------|-----|--------|
| MSFT | BUY | Call Debit Spread 510/520 | 7.0 | ✅ Open |
| SPY | BUY | Call Debit Spread 768/775 | 7.35 | ✅ Open |
| QQQ | BUY | Call Debit Spread 714/724 | 3.3 | Open (manual) |

**Image** : Terminal screenshot showing submitted orders with IDs. Or the Positions tab from the TEDA dashboard.

---

## Slide 10 — Tech Stack & Thank You

**Title** : TEDA — Tech Stack

**Text** (logos or text):

```
🐍 Python 3.14    📊 pandas/numpy    🦙 alpaca-py
🔌 Alpaca MCP      ⌨️ Alpaca CLI      🧠 Featherless (Llama 3.1)
📈 Streamlit       ☁️ Koyeb (24/7)    🔒 Paper Trading
```

**Links** :
- GitHub : `github.com/gedenedavid-ops/trade`
- Dashboard : `[Koyeb URL]`

**Footer** : Thank you — Questions?  
Hackathon lablab.ai × Alpaca · September 2026

**Image** : None. Just tech logos/icons.

---

## Image Capture Checklist

| Slide | Image to capture | Source |
|-------|-----------------|--------|
| 2 | Busy SPY chart (candles) | TradingView / Yahoo Finance |
| 6 | P&L widget from dashboard | TEDA Dashboard |
| 7 | Architecture diagram | Create in Canva (boxes + arrows) |
| 8 | Full dashboard screenshot | TEDA Dashboard (market open) |
| 9 | Positions tab or terminal log | TEDA Dashboard or terminal |
| 1, 3, 4, 5, 10 | No image (Canva design only) | — |