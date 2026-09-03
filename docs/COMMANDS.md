# TEDA — Guide d'utilisation

> Manuel rapide : toutes les commandes, ce qu'elles font, et comment lire
> les résultats. Mis à jour le 2 septembre 2026.

---

## Commandes

### 1. Smoke-test (données synthétiques)

```bash
python run_demo.py
```

**Utilité :** vérifier que tout le code compile et que les 5 modules de la
stratégie tournent sans erreur. Utilise des données inventées (pas le marché
réel). Utile après une mise à jour du code.

### 2. Scan dry-run (analyse sans ordre)

```bash
python -m agent.main                        # les 10 actifs par défaut
python -m agent.main --symbols SPY QQQ NVDA # actifs spécifiques
python -m agent.main --no-llm               # sans IA (plus rapide)
```

**Utilité :** lancer l'agent sur des vrais actifs Alpaca. Il analyse tout,
affiche les signaux, journalise les décisions, mais **ne passe aucun ordre**.
C'est le mode à utiliser pour surveiller le marché.

**Ce que tu vois pour un BUY valide :**

```
Analyse de NVDA ...
  [NVDA] biais=bullish  signal=BUY  @ 224.71
           -> HTF bias bullish | zone demand @ 221.77-224.21 | ...
           entrée 221.77-224.21 | SL 221.526 | TP 233.238 | RR 7.0
  -> PAPER ORDER (dry-run) | risque max $1000.00 | ...
```

| Ligne | Signification |
|-------|--------------|
| `biais=bullish` | Structure D1 haussière (HH + HL) |
| `signal=BUY` | Les 5 filtres sont tous verts → signal |
| `signal=NONE` | Au moins 1 filtre manque → pas d'entrée |
| `zone demand @ x-y` | Zone d'achat identifiée (OB) |
| `FVG bullish @ x-y` | Déséquilibre prix confirme la zone |
| `liquidity swept (clean)` | Stops nettoyés → zone fiable |
| `inducement` | Stops encore devant → piège, on n'entre pas |
| `entrée` | Range de prix pour l'ordre |
| `SL` | Stop loss (invalidation technique) |
| `TP` | Take profit (liquidité ou fallback 1:7) |
| `RR` | Ratio gain/risque (min 7.0) |
| `risque max` | 1% de l'equity |

### 3. Scan LIVE (passe de vrais ordres paper 💥)

```bash
python -m agent.main --live                     # les 10 actifs
python -m agent.main --symbols NVDA --live      # un seul actif
```

**Utilité :** ⚠️ **Mode réel.** L'agent :
1. Vérifie les positions ouvertes (sortie SL/TP automatique)
2. Scanne les 10 actifs
3. Si signal BUY/SELL avec RR >= 7 : construit un **debit spread** (MLEG)
   et le soumet sur Alpaca paper
4. Traque la position pour sortie auto

**Ce que tu vois :**

```
  [exit] 0 ouverte(s), 0 fermée(s)
  ...
  [NVDA] biais=bullish  signal=BUY  @ 224.71
  -> PAPER ORDER (live) | risque max $1000.00
  -> spread soumis : abc-def | 2 jambes
       NVDA260904C00225000
       NVDA260904C00235000
  [exit] position tracked: abc-def (NVDA)
```

### 4. Générer le rapport PDF

```bash
python generate_report.py
```

**Utilité :** rapport complet de l'état du projet. À chaque fin de session.
**Fichier :** `docs/Rapport_JJ_Mois_AAAA.pdf`

### 5. CLI Alpaca (terminal rapide)

```bash
python -m cli account      # résumé du compte (équité, P&L, cash, BP)
python -m cli status        # horloge marché + résumé compte
python -m cli positions     # positions ouvertes (depuis Alpaca)
python -m cli orders        # 10 derniers ordres
python -m cli watchlist     # scan SMV des 10 actifs (tableau)
python -m cli export        # export CSV de la watchlist
```

**Utilité :** commandes rapides sans lancer le dashboard. Utile en SSH,
cron jobs, ou pour vérifier l'état du compte en une ligne.

**Trade manuel (⚠️ marché ouvert uniquement) :**

```bash
python -m cli trade SPY BUY     # trade manuel (suit le signal SMV)
python -m cli trade QQQ SELL
```

**Contrôle de l'agent :**

```bash
python -m cli agent start       # démarrer l'agent en boucle auto
python -m cli agent stop        # créer un signal d'arrêt
```

---

## Comment lire le journal des trades

Après chaque session, le journal est mis à jour ici :

```
logs/trades.md
```

Exemple d'entrée :

```markdown
## 2026-08-31 16:42:45 UTC — BUY QQQ
- **Action** : PAPER ORDER (dry-run)
- **Prix** : 714.48
- **Biais** : bullish
- **Filtres** : 5/5 OK
- **Entrée** : 712.88 - 714.31
- **SL / TP** : 712.74 / 724.34
- **RR** : 12.52
- **Confiance** : high
- **Analyse IA** : Le signal indique un achat sur QQQ...
```

---

## Les 5 filtres — Résumé rapide

Quand tu vois `signal=NONE`, la raison te dit quel filtre a bloqué :

| Raison | Filtre manquant | Ce que ça veut dire |
|--------|----------------|---------------------|
| `No clear HTF bias (consolidation)` | Filtre 1 | Le marché est en range → l'agent essaie un Iron Condor |
| `No unmitigated demand zone` | Filtre 2 | Pas de zone d'achat valide sur le LTF |
| `Zone not confirmed by an imbalance` | Filtre 3 | La zone n'est pas confirmée par un FVG |
| `liquidity state = inducement` | Filtre 4 | Les stops sont encore devant → piège |
| `No market shift on LTF` | Filtre 5 | Pas de confirmation de changement de tendance |

### Signal IRON_CONDOR (consolidation)

Quand le biais est neutre ET qu'il y a un range clair (support + résistance),
l'agent émet un signal `IRON_CONDOR` au lieu de `NONE`. Le dashboard affiche
🟡 IRON CONDOR avec le range détecté.