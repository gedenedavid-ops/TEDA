# TEDA — Slide Deck (10 slides · Hackathon lablab.ai × Alpaca)

> Utilise ce contenu pour créer tes slides sur Canva.
> Chaque slide indique l'image/screenshot à capturer.

---

## Slide 1 — Cover

**Titre** : TEDA  
**Sous-titre** : Options Alpha Agent — Smart Money Vision × Alpaca  
**Bas de page** : Hackathon lablab.ai × Alpaca · Septembre 2026  

**Image** : Logo TEDA (tu peux utiliser un fond dégradé noir/vert foncé avec le texte en blanc — style terminal/trading). Format épuré, pas d'image.

---

## Slide 2 — Le Problème

**Titre** : Pourquoi un agent autonome ?

**Texte** :
- Le marché options US est complexe — trop de bruit pour un humain seul
- Les setups techniques apparaissent et disparaissent en minutes
- La discipline (risk management) est difficile à tenir manuellement
- Un agent ne dort pas, n'hésite pas, ne dévie pas des règles

**Image** : Screenshot d'un graphique SPY avec beaucoup de bougies (montre le "bruit" du marché). Source : TradingView ou Yahoo Finance.

---

## Slide 3 — Ce que fait TEDA

**Titre** : TEDA en 3 chiffres

**Texte** (3 colonnes) :

| 🔭 | ⚡ | 🛡️ |
|---|---|---|
| **10 actifs** | **5 minutes** | **5 filtres** |
| surveillés 24/7 | par cycle d'analyse | avant chaque trade |

- Scan automatique toutes les 5 minutes
- Détection des déséquilibres institutionnels (Smart Money)
- Exécution multi-legs options (debit spreads + iron condors)
- Sortie automatique SL/TP

**Image** : Pas d'image — garder épuré avec les 3 métriques en grand.

---

## Slide 4 — La Stratégie SMV (5 filtres)

**Titre** : La chaîne SMV — 5 filtres, aucun compromis

**Texte** (flow de gauche à droite ou de haut en bas) :

```
① Biais HTF (D1)  →  ② Zone OB (H1)  →  ③ FVG (H1)  →  ④ Liquidité sweepée  →  ⑤ Market Shift LTF  →  ✅ ENTRÉE
```

| Filtre | Question | Règle |
|--------|----------|-------|
| ① Biais | Tendance ? | HH+HL = bullish 80/20 |
| ② Zone OB | Où agir ? | Zone non mitigée |
| ③ FVG | Confirmé ? | Imbalance valide la zone |
| ④ Liquidité | Piège ou safe ? | Sweepée = clean, sinon inducement |
| ⑤ Shift LTF | Déclencher ? | BOS dans le sens du biais |

**Si 1 filtre manque → NONE (pas de trade).**

**Image** : Un flow diagram simple (flèches entre 5 blocs), ou juste le tableau ci-dessus mis en forme sur Canva avec des couleurs vertes/rouges.

---

## Slide 5 — Stratégies Options (B/B/B)

**Titre** : 3 signaux → 3 stratégies options

**Texte** :

```
🟢 BUY  →  Call Debit Spread
           (achat call ATM + vente call OTM)
           Risque défini, profit capé au spread width

🔴 SELL →  Put Debit Spread
           (achat put ATM + vente put OTM)
           Même structure, direction baissière

🟡 NEUTRAL →  Iron Condor
              (vente put spread + vente call spread)
              Range trading, crédit encaissé
```

**Image** : Diagrammes P&L simplifiés pour chaque stratégie :
- Call Debit Spread : courbe qui monte après le strike long
- Put Debit Spread : courbe qui monte sous le strike long
- Iron Condor : courbe en "tente" avec profit max au centre

Tu peux les faire directement dans Canva avec des formes simples (pas besoin de screenshot).

---

## Slide 6 — Gestion du Risque

**Titre** : Risk Gates — La discipline avant le profit

**Texte** (3 blocs) :

```
🔒 1% max par trade
   $1,000 sur $100k equity
   Calculé automatiquement

📐 RR minimum 1:7
   Trade rejeté si ratio < 7
   Fallback TP intégré

🚪 Sortie automatique
   SL = invalidation technique
   TP = liquidité ou 1:7
   Check à chaque cycle (5 min)
```

**Image** : Un dashboard widget montrant le P&L avec une petite perte (-0.13% sur le screenshot du 3 sept). Capture le widget équité du dashboard TEDA.

---

## Slide 7 — Infrastructure Alpaca

**Titre** : Stack Alpaca — 3 briques

**Texte** (3 colonnes) :

| 📡 Trading API | 🔌 MCP Server | ⌨️ CLI |
|---|---|---|
| Données OHLCV IEX | IA connectée à Alpaca | Commandes terminal |
| Ordres MLEG options | Positions en temps réel | `python -m cli account` |
| Paper trading $100k | Débug API sans IDE | `python -m cli watchlist` |

+ **Featherless** : LLM open-source (Llama 3.1 8B) pour le raisonnement  
+ **Koyeb** : Déploiement 24/7, auto-deploy depuis GitHub  
+ **Streamlit** : Dashboard interactif 4 onglets

**Image** : Diagramme d'architecture simple :
```
[Alpaca API] ←→ [Agent TEDA] ←→ [Featherless LLM]
                    ↓
              [Dashboard Streamlit] → [Koyeb 24/7]
```

Fais-le dans Canva avec des boîtes et des flèches.

---

## Slide 8 — Dashboard Live

**Titre** : Monitoring 24/7

**Image** : **Screenshot complet du dashboard TEDA** (l'écran Streamlit avec les 4 onglets visibles, idéalement l'onglet Watchlist avec les signaux). 

Capture à faire quand le marché est ouvert pour avoir des données live.

**Mini-texte** en bas du slide : Dashboard Streamlit hébergé sur Koyeb — rafraîchissement auto 60s.

---

## Slide 9 — Résultats Live

**Titre** : Premiers trades — 3 septembre 2026

**Texte** :

| Actif | Signal | Stratégie | RR | Statut |
|-------|--------|-----------|-----|--------|
| MSFT | BUY | Call Debit Spread 510/520 | 7.0 | ✅ Ouvert |
| SPY | BUY | Call Debit Spread 768/775 | 7.35 | ✅ Ouvert |
| QQQ | BUY | Call Debit Spread 714/724 | 3.3 | Ouvert (manuel) |

**Image** : Screenshot du terminal montrant les ordres soumis avec les IDs. Ou screenshot de l'onglet Positions du dashboard TEDA.

---

## Slide 10 — Tech Stack & Thank You

**Titre** : TEDA — Stack technique

**Texte** (logos ou texte) :

```
🐍 Python 3.14    📊 pandas/numpy    🦙 alpaca-py
🔌 Alpaca MCP      ⌨️ Alpaca CLI      🧠 Featherless (Llama 3.1)
📈 Streamlit       ☁️ Koyeb (24/7)    🔒 Paper Trading
```

**Liens** :
- GitHub : `github.com/gedenedavid-ops/trade`
- Dashboard : `[URL Koyeb]`

**Bas de page** : Merci — Questions ?  
Hackathon lablab.ai × Alpaca · Septembre 2026

**Image** : Aucune. Juste les logos/icônes des technos.

---

## Récapitulatif des images à capturer

| Slide | Image à capturer | Source |
|-------|-----------------|--------|
| 2 | Graphique SPY chargé (bougies) | TradingView / Yahoo Finance |
| 6 | Widget P&L du dashboard | Dashboard TEDA |
| 7 | Diagramme architecture | À créer dans Canva (boîtes + flèches) |
| 8 | Screenshot complet du dashboard | Dashboard TEDA (marché ouvert) |
| 9 | Onglet Positions ou log terminal | Dashboard TEDA ou terminal |
| 1, 3, 4, 5, 10 | Aucune image (design Canva uniquement) | — |