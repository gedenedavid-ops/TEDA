# 🧭 Rôles & Responsabilités — Agent SMV × Alpaca

> Qui fait quoi ? Document clair pour éviter le mélange des tâches.
> Gedene = code & infra | Trader = stratégie & validation

---

## 👨‍💻 Gedene (Développeur / Coordinateur)

### Ce que tu fais :
- **Coder** l'agent : les 5 modules de la chaîne SMV, l'exécution des ordres, le dashboard
- **Déployer** l'agent sur un serveur 24/7 (Render/Koyeb) pour que le trader puisse le voir
- **Débugger** les erreurs (API Alpaca, calculs, contrats options expirés, etc.)
- **Surveiller** la santé technique : l'agent tourne-t-il ? Les ordres passent-ils ?
- **Intégrer** les retours du trader dans le code (ajustements de paramètres, nouveaux filtres)
- **Préparer la soumission** : compte paper neuf $100k, vidéo, one-page write-up, repo public

### Ce que tu ne fais pas :
- Décider si un signal est bon ou mauvais → c'est le trader
- Choisir les actifs à trader → c'est le trader
- Modifier les règles de risque (1%, 1:7) sans l'accord du trader

---

## 📊 Trader (Stratège SMV)

### Ce que le trader doit faire :
- **Définir** la stratégie : règles d'entrée, filtres, timeframes, paires de devises/actifs
- **Valider** les signaux : regarder le dashboard, confirmer que les BUY/SELL émis par l'agent sont cohérents avec la stratégie SMV
- **Ajuster** les paramètres : si trop de signaux ou pas assez, si les zones OB sont mal détectées, si le RR de 7 est trop restrictif
- **Analyser** le P&L : les trades gagnants vs perdants, pourquoi, que corriger
- **Décider** des priorités : on se concentre sur quels actifs ? On active l'Iron Condor ? On backteste ?

### Ce que le trader ne fait pas :
- Coder → c'est Gedene
- Lire les logs techniques → c'est Gedene
- Gérer les clés API, le serveur, les bugs Python → c'est Gedene

---

## 🔄 Communication

- **WhatsApp** pour les décisions rapides
- **Dashboard Streamlit** pour que le trader voie les signaux en direct
- **Ce repo GitHub** = source de vérité du code

---

## 📋 Questions ouvertes — En attente du trader

| # | Question | Contexte |
|---|----------|----------|
| 1 | **Validation ETFs forex** | FXE (EURUSD), FXB (GBPUSD), FXY (USDJPY), GLD (XAUUSD), IWM (GBPJPY), MSFT (EURGBP). Le trader valide ces remplacements ? |
| 2 | **Priorité actifs** | Après SPY/QQQ/MSFT/NVDA, on priorise quels actifs ? |
| 3 | **Iron Condor** | On active la stratégie consolidation (Iron Condor) maintenant ou plus tard ? |
| 4 | **Fréquence de la boucle** | Actuellement 5 minutes entre chaque cycle. Le trader valide ? |
| 5 | **Backtest** | Le trader veut un backtest sur les 6 derniers mois ? |
| 6 | **Prochaines étapes** | Quelle est la priorité du trader pour les prochains jours avant la soumission (4 septembre) ? |