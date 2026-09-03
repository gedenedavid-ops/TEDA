# TEDA — One-Page Write-Up

**Hackathon** : Options Alpha Agents — lablab.ai × Alpaca  
**Projet** : TEDA (Trading Agent)  
**Date** : Septembre 2026  
**Compte Paper** : $100,000 — Alpaca Paper Trading  

---

## 1. AI Logic : La chaîne SMV en 5 filtres

TEDA ne prédit pas le marché. Il applique une stratégie **Smart Money Vision (SMV)**
déterministe, adaptée du SMC/ICT/Wyckoff, en 5 étapes séquentielles :

| Filtre | Timeframe | Règle | Rôle |
|--------|-----------|-------|------|
| 1. Biais directionnel | D1 | HH+HL = bullish (80% impulsion, 20% retracement). LH+LL = bearish. | Filtre de direction |
| 2. Zone OB (Offre/Demande) | H1 | Zone non mitigée du bon type (demande pour BUY, offre pour SELL). Origine : manipulative, money take, breaker. | Zone d'intervention |
| 3. Imbalance (FVG) | H1 | Fair Value Gap qui confirme la zone OB. L'imbalance n'est jamais un signal isolé. | Confirmation |
| 4. Liquidité sweepée | H1/M15 | Liquidité externe (EQL/EQH) déjà nettoyée par une mèche = zone prioritaire. Liquidité encore devant = inducement (piège). | Tri des zones |
| 5. Market Shift LTF | M15 | Break of Structure (BOS) dans le sens du biais HTF sur le timeframe inférieur. | Trigger d'entrée |

**Si les 5 filtres passent → BUY ou SELL.**  
**Si le biais est neutre (consolidation) → Iron Condor (range ≥ 1.5%).**  
**Sinon → NONE (aucun trade).**

L'agent ne prend **aucune** décision discrétionnaire. Le LLM (Featherless,
Meta-Llama-3.1-8B) sert uniquement à la **journalisation et au raisonnement
explicatif** — il ne pilote jamais l'exécution.

---

## 2. Risk Gates : Gestion du risque

Chaque trade est soumis à 3 barrières de risque avant exécution :

| Barrière | Valeur | Implémentation |
|----------|--------|----------------|
| Risque max / trade | **1%** de l'equity ($1,000 sur $100k) | `risk.compute_risk_amount()` |
| Risk/Reward minimum | **1:7** | `risk.check_rr_ratio()` — rejet automatique si RR < 7 |
| Position max | **25%** de l'equity | Vérifié avant chaque ordre |

**Stop Loss** : niveau d'invalidation technique SMV (cassure de la zone OB).  
**Take Profit** : liquidité technique (EQH/EQL/swing) ou fallback calculé à 1:7.  
**Sortie automatique** : `agent/exit.py` surveille les positions à chaque cycle
(5 min) et ferme si SL ou TP est atteint.

**Anti-doublon** : une seule position par symbole. Si une position est déjà
ouverte sur SPY, l'agent skip le signal suivant.

**Stratégies options (B/B/B)** :
- BUY → **Call Debit Spread** (achat call + vente call plus haut)
- SELL → **Put Debit Spread** (achat put + vente put plus bas)
- Consolidation → **Iron Condor** (vente put spread + vente call spread)

---

## 3. Alpaca Infrastructure Implementation

TEDA utilise les 3 briques technologiques Alpaca :

### Trading API (`alpaca-py`)
- **Données** : flux IEX (gratuit) — OHLCV quotidien (D1, 400 barres) + horaire
  (H1, 500 barres) pour les 10 actifs de la watchlist.
- **Ordres** : ordres multi-legs (MLEG) pour les debit spreads et iron condors.
  Les ordres sont des **Limit Orders** (DAY) pour éviter le slippage.
- **Compte** : paper trading, $100,000 de capital initial, niveau d'options 3.

### MCP Server (`@alpacahq/alpaca-mcp-server`)
- Utilisé pendant le développement pour que l'IA (Claude/Cursor) puisse :
  - Inspecter les positions en temps réel après chaque trade
  - Consulter la chaîne d'options pour valider les strikes disponibles
  - Déboguer les erreurs API sans quitter l'IDE
- Configuration fournie dans `mcp/alpaca-mcp.json` — prête à l'emploi.

### CLI Alpaca (`python -m cli`)
- Module CLI complet exposant les commandes Alpaca :
  - `account` — résumé du compte (équité, P&L, cash, buying power)
  - `positions` — positions ouvertes
  - `orders` — 10 derniers ordres
  - `watchlist` — scan SMV des 10 actifs avec tableau des filtres
  - `status` — horloge marché + résumé compte
  - `trade SYM BUY/SELL` — trade manuel
  - `agent start/stop` — contrôle de l'agent autonome
  - `export` — export CSV de la watchlist

### Déploiement 24/7
- **Koyeb** (tier gratuit eMicro : 0.25 vCPU, 512 MB RAM)
- **Dashboard Streamlit** accessible en continu, avec 4 onglets :
  Watchlist, Positions, Historique, Stratégie
- **Agent** tourne en sous-processus détaché (survit aux refreshs de page)
- **Cycle** : analyse des 10 actifs toutes les 5 minutes
- **Déploiement auto** : push GitHub → Koyeb redeploie

### Watchlist (10 actifs)
| Stocks/ETFs | Forex (via ETFs) |
|-------------|------------------|
| SPY, QQQ, NVDA, AAPL, MSFT, IWM | FXE (EURUSD), FXB (GBPUSD), FXY (USDJPY), GLD (XAUUSD) |

---

## Résultats

L'agent a exécuté ses premiers trades le 3 septembre 2026 :
- **MSFT BUY** — Call Debit Spread 510/520 (RR 7.0)
- **SPY BUY** — Call Debit Spread 768/775 (RR 7.35)
- **QQQ BUY** — Call Debit Spread 714/724 (RR 3.3, entré manuellement)

L'agent continue de trader en autonomie sur Koyeb, 24h/24, jours de marché.