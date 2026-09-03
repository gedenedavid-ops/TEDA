# Stratégie SMV (Smart Money Vision)

> Adaptation au marché actions/options de la stratégie SMC du trader
> (source : PDF "ULTRA BOOK FX 2", 44 pages).

## Les 4 piliers

1. **Structure** (la reine) — biais directionnel 80% impulsion / 20% retracement
2. **Offre & Demande** — zones OB (bougie manipulatrice + bougie qui prend l'argent)
3. **Cause & Effet** — accumulation/distribution, Wyckoff Phases A→E
4. **Liquidité** — EQL/EQH, signatures, inducement, sweep

## Règles d'or

| Règle | Valeur |
|-------|--------|
| Risque max / trade | 1% |
| Risk/Reward min | 1:7 |
| Stop Loss | serré (zone invalidée) |

## Chaîne d'entrée (5 filtres)

```
Structure HTF (biais 80%)  →  Zone OB  →  Imbalance (confirme)  →  Liquidité (sweep)  →  Market Shift LTF  →  ENTRÉE
```

### Détail du sweep (règle clé)
- **Zone "clean"** : liquidité externe déjà sweepée → zone **prioritaire**
  d'intervention (piège purgé).
- **Zone "inducement"** : liquidité encore devant → **piège**, à éviter.

## Mapping Forex → Options

| Concept SMV | Traduction options |
|-------------|-------------------|
| Structure bullish (80%) | Buy Call / Call debit spread / Sell Put |
| Structure bearish (80%) | Buy Put / Put debit spread / Sell Call |
| Consolidation / Wyckoff B | Iron Condor / Short Strangle (theta) |
| Wyckoff Phase C (Spring/UTAD) | Entrée directionnelle |
| Zones OB / FVG | Strikes + niveaux d'entrée/sortie |

## Timeframes

| Usage | Timeframe |
|-------|-----------|
| Structure + 80/20 | D1 / H4 |
| Zones OB / POI | H4 / H1 |
| Imbalance + Liquidité + Market Shift | H1 / M15 |

## Statut

- [x] Chaîne 5 filtres codée et validée sur données réelles SPY
- [ ] Choix des sous-jacents
- [ ] Backtest complet
- [ ] Optimisation des paramètres (lookback, tolérance EQL, DTE)
