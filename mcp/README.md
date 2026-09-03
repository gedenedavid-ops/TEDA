# MCP Server — Alpaca × TEDA

Le **Model Context Protocol (MCP)** permet à un assistant IA (Claude, Cursor, VS Code,
ChatGPT) d'interagir directement avec l'API Alpaca via des outils structurés.

## Pourquoi MCP dans TEDA ?

- **Développement assisté** : Pendant le hackathon, nous avons utilisé le MCP Server
  Alpaca pour que l'IA puisse vérifier les positions, consulter le compte, et tester
  des ordres en paper trading sans quitter l'IDE.
- **Exigence hackathon** : Le règlement impose l'utilisation du MCP Server ou du CLI
  Alpaca. TEDA satisfait les deux.
- **Déploiement** : Le MCP Server peut être connecté à l'agent TEDA pour du
  raisonnement augmenté sur les décisions de trading.

## Installation

### Prérequis

- Node.js ≥ 18
- Un compte Alpaca Paper (clés API dans `.env`)

### Setup

```bash
# 1. Installer le MCP server Alpaca (global ou local)
npm install -g @alpacahq/alpaca-mcp-server

# 2. Configurer les variables d'environnement
export ALPACA_API_KEY="PK..."
export ALPACA_SECRET_KEY="..."
export ALPACA_PAPER="true"
```

### Configuration IDE

**Cursor / VS Code** : Ajouter au fichier `~/.cursor/mcp.json` ou `~/.vscode/mcp.json` :

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "npx",
      "args": ["-y", "@alpacahq/alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "PK...",
        "ALPACA_SECRET_KEY": "...",
        "ALPACA_PAPER": "true"
      }
    }
  }
}
```

**Claude Desktop** : Utiliser le fichier `mcp/alpaca-mcp.json` fourni.

## Outils MCP disponibles

Une fois connecté, l'IA a accès à :

| Outil | Description |
|-------|-------------|
| `get_account` | Résumé du compte (équité, BP, P&L) |
| `get_positions` | Positions ouvertes |
| `get_orders` | Ordres récents |
| `place_order` | Placer un ordre (paper) |
| `cancel_order` | Annuler un ordre |
| `get_bars` | Récupérer des données OHLCV |
| `get_clock` | Horloge du marché |
| `get_option_chain` | Chaîne d'options pour un sous-jacent |

## Utilisation avec TEDA

Pendant le développement, nous avons utilisé le MCP Server pour :

1. **Vérifier les positions** après chaque trade pour confirmer l'exécution
2. **Consulter la chaîne d'options** pour valider les strikes disponibles
3. **Tester des ordres** en paper avant de les intégrer dans le code
4. **Déboguer** les erreurs API en inspectant les réponses en temps réel

## Références

- [Alpaca MCP Server — Documentation officielle](https://docs.alpaca.markets/us/docs/mcp-server)
- [MCP Protocol — Spécification](https://modelcontextprotocol.io)
- [Alpaca Trading API](https://docs.alpaca.markets/us/docs/trading-api)