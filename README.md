# Options Alpha Agents 🦙

Agent de trading autonome basé sur **Alpaca** (paper trading) pour le
hackathon **Options Alpha Agents** (lablab.ai × Alpaca).

L'agent adapte la stratégie **SMV (Smart Money Vision)** — une approche
SMC/ICT — au marché des **options actions**, en exploitant le Trading API,
le **CLI Alpaca**, et un LLM open-source via **Featherless** pour le
raisonnement.

## Documentation

- [Journal des décisions](docs/DECISIONS.md) — chaque décision, datée et justifiée
- [Stratégie SMV](docs/STRATEGY.md) — les règles et le mapping Forex→Options
- [Architecture](docs/ARCHITECTURE.md) — vue technique du projet

## Installation

```bash
pip install -r requirements.txt
cp config/.env.example config/.env
# remplir ALPACA_API_KEY / ALPACA_SECRET_KEY (paper)
```

## Utilisation

```bash
# Smoke-test du moteur stratégie (données synthétiques)
python run_demo.py
```

## Structure

```
strategy/    cœur SMV (structure, zones OB, imbalance, liquidité, triggers)
data/        récupération OHLCV Alpaca
execution/   client Alpaca + mapping options
agent/       boucle autonome, LLM, gestion du risque
config/      configuration (.env)
docs/        documentation
```

## Avertissement

Projet éducatif en **paper trading** uniquement. Aucun capital réel engagé.
Le trading d'options comporte un risque élevé de perte.
