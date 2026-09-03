# TEDA — Journal des décisions

> Document vivant : chaque décision technique ou stratégique est datée et
> consignée ici, avec la raison derrière le choix. C'est la source de vérité
> pour la one-page write-up de la soumission finale.
>
> **Projet** : TEDA (Trading Agent) — Hackathon lablab.ai × Alpaca, Septembre 2026

---

## 2026-08-31 — Kick-off du projet

### D01 — Stack technique : Python + SDK Alpaca
- **Décision** : Python + `alpaca-py` (SDK officiel) + Alpaca CLI.
- **Raison** : écosystème data/ML mature, SDK officiel bien documenté, CLI
  disponible pour l'exigence du hackathon (MCP **ou** CLI → on a choisi CLI).
- **Alternative écartée** : JavaScript/TypeScript (moins adapté au calcul
  technique pur).

### D02 — IA : Featherless (open-source) plutôt qu'OpenAI/Claude
- **Décision** : inférence LLM open-source via Featherless (endpoint
  compatible OpenAI).
- **Raison** : $25 de crédits offerts par le partenaire Featherless + aligné
  avec l'esprit "build in public". Modèle par défaut : `Meta-Llama-3.1-8B-Instruct`.
- **Note** : le LLM sert au **raisonnement + journalisation**, pas à
  l'exécution directe (les décisions de trade restent pilotées par les règles
  SMV déterministes).

### D03 — Stratégie : SMV (Smart Money Vision) adaptée du Forex
- **Décision** : adapter la stratégie SMV du trader (PDF 44 pages) au marché
  actions/options Alpaca.
- **Raison** : c'est l'expertise du trader. Le SMC/ICT est transférable aux
  actions via les mêmes concepts (structure, offre/demande, liquidité).
- **Adaptation clé** : le forex (pips/positions) devient des **options**
  (calls/puts directionnels + spreads en consolidation).

### D04 — Timeframes (paires HTF/LTF)
- **Décision** :
  - Structure + règle 80/20 : **D1 / H4**
  - Zones OB / POI majeurs : **H4 / H1**
  - Imbalance + Liquidité + Market Shift : **H1 / M15** (M5 pour trigger fin)
- **Raison** : fractalité de la structure SMV — le biais HTF filtre, le LTF
  affine l'entrée. Validé par le trader.

### D05 — Chaîne d'entrée : 5 filtres ordonnés
- **Décision** : une entrée exige les 5 filtres en séquence :
  1. Biais HTF (80% d'impulsion)
  2. Zone OB non mitigée du bon type (demande pour BUY, offre pour SELL)
  3. Imbalance (FVG) qui confirme la zone
  4. Liquidité externe déjà sweepée ("clean", pas "inducement")
  5. Market Shift LTF
- **Raison** : validée à 100% par le trader. L'imbalance n'est **pas** un
  signal isolé : elle **confirme** une zone OB. La liquidité sert de **tri**
  des zones.

### D06 — Règle de sweep (priorité vs piège)
- **Décision** :
  - Zone OB dont la liquidité externe sous-jacente a déjà été sweepée =
    **zone prioritaire** (piège purgé).
  - Zone dont la liquidité réside toujours devant = **inducement** (piège).
- **Raison** : c'est le cœur du Smart Money — on n'achète qu'après la purge
  des stops, jamais dans le piège.

### D07 — Flux de données : IEX (gratuit) accepté pour le dev
- **Décision** : utiliser le flux IEX (gratuit) malgré sa limite (~15 jours
  d'intraday, ~2,7 ans de daily).
- **Raison** : suffisant pour générer des signaux en live et tester la
  chaîne. Le trader valide : "on teste, on verra la suite, on corrigera".
- **Réévaluation possible** : souscription SIP (payant) si le backtest
  intraday l'exige.

### D08 — Compte paper : $100,000, options niveau 3
- **Décision/État** : compte paper dédié, balance $100,000 (requis par le
  hackathon), approbation options **niveau 3** (calls, puts, spreads).
- **Rappel** : pour la **soumission finale**, créer un compte neuf dédié
  (les comptes réutilisés ne sont pas éligibles au jugement).

### D09 — Gestion du risque (règles SMV)
- **Décision** :
  - Risque **1% max / trade**
  - Risk/Reward **minimum 1:7**
  - Position **max 25%** de l'equity
- **Raison** : règles d'or du PDF SMV, transposées au sizing options.

---

## 2026-09-02 — Mise en production & corrections critiques

### D10 — Watchlist : 10 actifs (stocks + ETFs forex)
- **Décision** : panier final de 10 sous-jacents : SPY, QQQ, NVDA, AAPL,
  FXE, FXB, FXY, GLD, IWM, MSFT.
- **Raison** : les 4 premiers sont les stocks/ETFs les plus liquides.
  FXE/FXB/FXY remplacent EURUSD/GBPUSD/USDJPY (non supportés par Alpaca)
  via des ETFs. GLD remplace XAUUSD. IWM et MSFT complètent pour
  diversification.
- **Statut** : en attente de validation par le trader pour les ETFs forex.

### D11 — Exécution : Call/Put Debit Spread (MLEG)
- **Décision** : BUY → Call Debit Spread, SELL → Put Debit Spread.
  Ordres multi-legs (MLEG) sur Alpaca.
- **Raison** : spreads = risque défini, cohérent avec RR 1:7. Les spreads
  combinent un strike proche de la zone d'entrée (jambe longue) et un strike
  proche du TP (jambe courte).
- **Correction** : `_place_paper_order()` utilisait encore `select_atm_contract()`
  (fonction supprimée). Reconnecté à `build_debit_spread()` le 2/9.

### D12 — Sortie automatique SL/TP (exit.py)
- **Décision** : module `agent/exit.py` pour surveiller les positions
  ouvertes et fermer automatiquement quand SL ou TP est atteint.
- **Fonctionnement** :
  - Traque les spreads ouverts dans `logs/positions.json`
  - À chaque cycle, vérifie le prix actuel vs SL/TP
  - Si hit : soumet des ordres de clôture (STC pour jambe longue, BTC pour
    jambe courte)
- **Raison** : exigence du trader — "sortie automatique si TP ou SL atteint".

### D13 — Fallback TP (minimum 1:7 RR)
- **Décision** : quand aucune liquidité technique (EQH/EQL/swing) n'est
  détectée pour le TP, calculer un TP de fallback à 1:7 minimum.
- **Raison** : NVDA a passé les 5 filtres mais TP=None → RR=None → trade
  rejeté. Sans fallback, des setups parfaits sont gaspillés.
- **Implémentation** : TP = entry_mid + (entry_mid - SL) * 7 pour BUY,
  TP = entry_mid - (SL - entry_mid) * 7 pour SELL.

### D14 — Premier signal live valide : NVDA BUY
- **Résultat** : le 2/9 à 17h UTC, NVDA a émis un BUY avec les 5 filtres.
  - Biais : bullish (D1)
  - Zone demand : 221.77-224.21 (H1)
  - FVG bullish : 217.97-221.21 (H1)
  - Liquidité : swept (clean)
  - Market shift LTF : confirmé
  - Entrée : 221.77-224.21 | SL : 221.526 | TP : 233.238 | RR : 7.0
  - Ce trade serait passé en live si `--live` était actif.

---

## 2026-09-03 — Dashboard, déploiement & stabilisation

### D15 — Fix TP/RR floating point (arrondi)
- **Décision** : arrondir `stop_loss` à 2 décimales, `take_profit` fallback à 2
  décimales, `rr_ratio` à 1 décimale dans `triggers.py`.
- **Raison** : le calcul `entry_mid + risk * 7.0` produisait des floats
  imprécis (ex: `774.6949999999999` au lieu de `774.70`). Les valeurs sont
  maintenant propres.

### D16 — Dashboard Streamlit avec agent intégré
- **Décision** : dashboard Streamlit (`dashboard.py`) avec 4 onglets
  (Watchlist, Positions, Historique, Stratégie). L'agent peut être lancé
  depuis la sidebar dans un thread en arrière-plan.
- **Raison** : le trader a besoin de visibilité 24/7 sur les signaux et
  le P&L sans avoir à se connecter au terminal.

### D17 — Déploiement Render/Koyeb
- **Décision** : déploiement sur Koyeb (tier gratuit eMicro, uptime continu) via `Procfile`.
  Variables d'environnement : `ALPACA_API_KEY`,
  `ALPACA_SECRET_KEY`, `FEATHERLESS_API_KEY`.
- **Raison** : hébergement 24/7 pour que l'agent et le dashboard soient
  accessibles en continu. Koyeb a été choisi car le tier gratuit ne spin-down
  pas (contrairement à Render), donc pas besoin de cron job de ping.
  Déploiement auto depuis GitHub.

### D18 — Premier trade multi-actifs (3 positions)
- **Résultat** : le 3/9 entre 14h23 et 15h04 UTC, 3 trades exécutés :
  - MSFT BUY (RR 7.0) : Call Debit Spread 510/520
  - SPY BUY (RR 7.35) : Call Debit Spread 768/775
  - QQQ BUY (RR 3.3) : Call Debit Spread 714/724 (RR sous le seuil mais
    entré manuellement)
- **Statut** : les 3 positions sont ouvertes sur Alpaca paper.
  P&L initial ~-$150 (normal, time decay des options).

### D19 — Fix ordre log vs anti-doublon
- **Décision** : réorganiser le flux dans `agent/main.py` pour que le
  message "PAPER ORDER (live)" ne s'affiche qu'après le check anti-doublon.
- **Raison** : le message "PAPER ORDER (live)" s'affichait même quand la
  position était skipped (déjà une position ouverte), créant de la confusion
  dans les logs.

### D20 — Trigger Iron Condor pour consolidation
- **Décision** : ajouter un trigger `evaluate_consolidation()` dans
  `strategy/triggers.py` qui détecte les phases de range et émet un
  signal `IRON_CONDOR`.
- **Conditions** :
  1. Support clair sous le prix (zone de demande ou swing low).
  2. Résistance claire au-dessus (zone d'offre ou swing high).
  3. Prix entre support et résistance.
  4. Range >= 2% du prix.
- **Fallback** : si le trigger directionnel (BUY/SELL) retourne NONE,
  l'agent essaie automatiquement le trigger consolidation.
- **Exécution** : le signal IRON_CONDOR appelle `build_iron_condor()`
  qui construit un Iron Condor à 4 jambes (STO put spread + STO call spread).
- **Gestion** : pas de check RR pour les Iron Condors (ce sont des spreads
  de crédit), pas de SL/TP traditionnel (géré par l'expiration).

### D21 — Module CLI Alpaca (`python -m cli`)
- **Décision** : créer un module CLI (`cli/`) qui expose les commandes
  Alpaca via le terminal, satisfaisant l'exigence hackathon.
- **Commandes** :
  - `python -m cli account` : résumé du compte (équité, P&L, cash, BP)
  - `python -m cli positions` : positions ouvertes
  - `python -m cli orders` : 10 derniers ordres
  - `python -m cli watchlist` : scan SMV des 10 actifs
  - `python -m cli status` : horloge marché + résumé compte
  - `python -m cli export` : export CSV de la watchlist
  - `python -m cli trade SYM BUY/SELL` : trade manuel
  - `python -m cli agent start/stop` : contrôle de l'agent autonome
- **Raison** : le CLI utilise le même `BrokerClient` que l'agent et le
  dashboard, garantissant une cohérence des données. C'est plus léger
  que le MCP server et mieux adapté aux sessions longues.

---

## Prochaines décisions (à consigner)

- [x] Fréquence de la boucle agent → 5 minutes (décidé par Gedene, en attente validation trader)
- [x] Iron Condor pour consolidation (trigger créé le 3/9 — D20)
- [x] Intégration CLI Alpaca (module créé le 3/9 — D21)
- [ ] Compte paper neuf pour soumission finale ($100k)
- [ ] Validation ETFs forex par le trader (D10)
- [ ] Backtest 3-6 mois
- [ ] Posts réseaux sociaux (X/LinkedIn — exigence sociale)
