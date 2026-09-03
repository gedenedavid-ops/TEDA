# TEDA — Trading Agent 🦙

Agent de trading autonome basé sur **Alpaca** (paper trading) pour le
hackathon **Options Alpha Agents** (lablab.ai × Alpaca, Septembre 2026).

**TEDA** adapte la stratégie **SMV (Smart Money Vision)** — une approche
SMC/ICT/Wyckoff — au marché des **options actions**, en exploitant :

- Le **Trading API** Alpaca (stocks + options)
- Le **CLI Alpaca** pour les opérations de gestion
- Le **MCP Server** Alpaca pour l'interaction agent
- Un LLM open-source via **Featherless** pour le raisonnement

## 🎯 Ce que fait TEDA

- Analyse 10 actifs toutes les 5 minutes (SPY, QQQ, NVDA, AAPL, MSFT, FXE, FXB, FXY, GLD, IWM)
- Détecte la structure de marché (biais 80/20, BOS, swing points)
- Identifie les zones d'offre/demande + Fair Value Gaps (imbalances)
- Évalue la liquidité (sweep vs inducement)
- Place des **Call/Put Debit Spreads** (options) quand les 5 filtres SMV sont alignés
- Gère le risque : 1% max par trade, RR minimum 1:7
- Dashboard Streamlit 24/7 hébergé sur **Koyeb**

## 📊 Dashboard

![TEDA Dashboard](https://img.shields.io/badge/Status-Live-brightgreen)

L'interface Streamlit affiche en temps réel :
- Watchlist avec signaux (BUY/SELL/NONE)
- Positions ouvertes (SL/TP)
- P&L et équité du compte
- Historique des trades
- Logs de l'agent

## 🚀 Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Remplir ALPACA_API_KEY / ALPACA_SECRET_KEY (paper trading)

# Lancer le dashboard
streamlit run dashboard.py

# Lancer l'agent en CLI (mode manuel)
python -m agent.main --live

# Boucle automatique toutes les 5 minutes
python -m agent.main --live --loop 5 --no-llm
```

## 📁 Structure

```
agent/          Boucle autonome, décision LLM, gestion du risque
strategy/       Cœur SMV (structure, zones OB, imbalance, liquidité, triggers)
data/           Récupération OHLCV Alpaca (IEX)
execution/      Client Alpaca + construction de spreads options
cli/            Commandes CLI Alpaca (account, watchlist, orders)
config/         Configuration (.env, settings)
docs/           Documentation complète
logs/           Positions trackées et statut de l'agent
```

## 📖 Documentation

| Document | Contenu |
|----------|---------|
| [Journal des décisions](docs/DECISIONS.md) | Toutes les décisions techniques, datées et justifiées (D01-D21+) |
| [Stratégie SMV](docs/STRATEGY.md) | Les règles de trading, la chaîne des 5 filtres |
| [Architecture](docs/ARCHITECTURE.md) | Vue technique du projet |
| [Guide des commandes](docs/COMMANDS.md) | Toutes les commandes CLI et leur utilisation |
| [Déploiement Koyeb](docs/DEPLOY.md) | Guide de déploiement 24/7 |

## 🛠️ Technologies

- **Alpaca** — Trading API, MCP Server, CLI
- **Featherless** — LLM open-source pour le raisonnement
- **Streamlit** — Dashboard interactif
- **Koyeb** — Hébergement 24/7 (tier gratuit)
- **Python 3.14** — pandas, numpy, alpaca-py, openai

## ⚠️ Avertissement

Projet éducatif en **paper trading** uniquement. Aucun capital réel engagé.
Le trading d'options comporte un risque élevé de perte. Les performances
passées ne préjugent pas des résultats futurs.

---

*Hackathon lablab.ai × Alpaca — Options Alpha Agents — Septembre 2026*