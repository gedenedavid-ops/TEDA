# 🔧 Déploiement 24/7 sur Koyeb

> TEDA — Streamlit dashboard + agent trading en continu

---

## Prérequis

- Un compte [Render](https://render.com) (gratuit, pas de carte bancaire)
- Le repo GitHub du projet (`GEDENE-OPS/trade`)

---

## Étape 1 : Pousser le projet sur GitHub

```bash
cd trade
git add -A
git commit -m "Ready for Koyeb deploy"
git push origin main
```

---

## Étape 2 : Déployer sur Koyeb

1. Va sur [app.koyeb.com](https://app.koyeb.com)
2. Clique **Create Service** → **Deploy from GitHub**
3. Connecte ton repo `gedenedavid-ops/trade`
4. Configure :
   - **Instance type** : eMicro (0.25 vCPU, 512 MB RAM) — gratuit en tier hobby
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `streamlit run dashboard.py --server.port 8000 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false`
   - **Port** : 8000
5. Clique **Deploy**

---

## Étape 3 : Variables d'environnement

Dans le dashboard Koyeb → **Settings** → **Environment Variables** → ajoute :

| Nom | Valeur |
|-----|--------|
| `ALPACA_API_KEY` | Ta clé API paper Alpaca |
| `ALPACA_SECRET_KEY` | Ta clé secrète paper Alpaca |
| `FEATHERLESS_API_KEY` | Ta clé Featherless (optionnelle) |

---

## Étape 4 : Utilisation

Une fois déployé :

1. Ouvre l'URL Koyeb (ex: `https://teda-xxx.koyeb.app`)
2. Dans la sidebar, clique **"▶️ Lancer l'agent"**
3. L'agent tourne en continu (cycle de 5 minutes) dans un sous-processus détaché
4. Les positions ouvertes, SL/TP et P&L sont visibles en temps réel
5. L'agent survit aux refreshs de page et continue de trader 24/7

---

## Avantages de Koyeb vs Render

- **Uptime continu** sur le tier gratuit (pas de spin-down après 15 min)
- **Déploiement auto** depuis GitHub (push = redeploy)
- **Health checks** et logs intégrés
- Le tier gratuit `eMicro` suffit largement pour TEDA (0.25 vCPU, 512 MB RAM)

---

## Fichiers créés pour le déploiement

- `Procfile` → configuration Koyeb
- `requirements.txt` → mis à jour avec `streamlit>=1.57`