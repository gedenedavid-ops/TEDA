# 🔧 Déploiement 24/7 sur Render (gratuit)

> Options Alpha Agent — Streamlit dashboard + agent trading en continu

---

## Prérequis

- Un compte [Render](https://render.com) (gratuit, pas de carte bancaire)
- Le repo GitHub du projet (`GEDENE-OPS/trade`)

---

## Étape 1 : Pousser le projet sur GitHub

```bash
cd trade
git add -A
git commit -m "Ready for Render deploy"
git push origin main
```

---

## Étape 2 : Déployer sur Render

### Option A — Via `render.yaml` (recommandé)

1. Va sur [dashboard.render.com](https://dashboard.render.com)
2. Clique **New +** → **Blueprint**
3. Connecte ton repo GitHub
4. Render détecte automatiquement `render.yaml` → clique **Apply**

### Option B — Manuellement

1. Va sur [dashboard.render.com](https://dashboard.render.com)
2. Clique **New +** → **Web Service**
3. Connecte ton repo GitHub
4. Configure :
   - **Name** : `options-alpha-agent`
   - **Region** : Frankfurt (plus proche de l'Europe/Abidjan)
   - **Branch** : `main`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false`

---

## Étape 3 : Variables d'environnement

Dans le dashboard Render → **Environment** → ajoute :

| Nom | Valeur |
|-----|--------|
| `ALPACA_API_KEY` | Ta clé API paper Alpaca |
| `ALPACA_SECRET_KEY` | Ta clé secrète paper Alpaca |
| `FEATHERLESS_API_KEY` | Ta clé Featherless (optionnelle) |

---

## Étape 4 : Utilisation

Une fois déployé :

1. Ouvre l'URL Render (ex: `https://options-alpha-agent.onrender.com`)
2. Dans la sidebar, clique **"▶️ Lancer l'agent"**
3. L'agent tourne en continu (cycle de 5 minutes) dans un thread en arrière-plan
4. Les positions ouvertes, SL/TP et P&L sont visibles en temps réel

---

## ⚠️ Limites du tier gratuit Render

- Le service se met en veille après **15 minutes d'inactivité** (pas de visiteurs)
- Pour garder l'agent actif 24/7, deux solutions :
  - Utiliser un **health check ping** (cron job qui visite l'URL toutes les 10 min)
  - Passer au tier **Starter** ($7/mois) pour un uptime 100%
- La boucle agent tourne côté serveur, donc même si personne ne regarde le dashboard, l'agent continue de trader tant que le service est up

---

## Alternative : Koyeb

[Même principe avec Koyeb](https://www.koyeb.com) (2 apps gratuites, uptime continu sur le tier gratuit). 
La commande de démarrage est identique : 
```
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

---

## Fichiers créés pour le déploiement

- `Procfile` → configuration Render/Koyeb
- `render.yaml` → blueprint Render (déploiement one-click)
- `requirements.txt` → mis à jour avec `streamlit>=1.57`