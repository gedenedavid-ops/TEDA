# TEDA — Architecture technique

## Vue d'ensemble

```
agent/main.py          → boucle autonome (à venir)
agent/decision.py      → raisonnement + journalisation LLM (Featherless, à venir)
agent/risk.py          → sizing 1% / RR 1:7 / max 25%

strategy/              → cœur SMV (déterministe)
  structure.py         → biais 80/20, BOS, swing points
  supply_demand.py     → zones OB + breaker blocks
  imbalance.py         → FVG / IPA (confirme les zones)
  liquidity.py         → EQL/EQH + sweep (tri des zones)
  triggers.py          → chaîne 5 filtres → BUY/SELL/NONE
  models.py            → dataclasses partagées

data/market_data.py    → OHLCV Alpaca → DataFrame (IEX, timeframes mappés)
execution/client.py    → wrapper TradingClient + StockHistoricalDataClient
execution/options.py   → signal → contrat option ATM
config/settings.py     → .env + paramètres
```

## Flux de données

```
Alpaca Paper (IEX feed)
   │  fetch_stock_bars(symbol, timeframe)
   ▼
DataFrame OHLCV (index = timestamp)
   │
   ├── HTF (1D)  → structure.analyze_structure() → biais 80/20
   ├── H4/H1     → supply_demand.detect_zones()  → zones OB
   ├── H1/M15    → imbalance / liquidity         → FVG + sweep
   └── triggers.evaluate_trigger()               → Signal (BUY/SELL/NONE)
```

## Dépendances

- `alpaca-py` — SDK Trading API + Market Data
- `pandas` / `numpy` — calcul OHLCV et détection de patterns
- `openai` — client pour Featherless (endpoint compatible OpenAI)
- `python-dotenv` — configuration via `.env`

## Contraintes connues

- **IEX (gratuit)** : ~15 jours d'intraday, ~2,7 ans de daily.
- **Python 3.14** : récent, mais tous les wheels sont dispos.
