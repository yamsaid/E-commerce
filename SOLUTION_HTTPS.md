# Solution au Problème HTTPS Persistant

## Problème
Votre navigateur continue d'essayer d'accéder à `https://127.0.0.1:8000` même après avoir configuré le serveur pour HTTP.

## Causes
1. **Cache du navigateur** - Le navigateur a mis en cache la redirection HTTPS
2. **Historique de navigation** - L'URL HTTPS est dans l'historique
3. **Favoris/Bookmarks** - L'URL HTTPS est sauvegardée
4. **Auto-complétion** - Le navigateur suggère automatiquement HTTPS

## Solutions

### Solution 1: Vider le Cache (Recommandée)

#### Chrome/Edge :
1. Appuyez sur **Ctrl + Shift + Delete**
2. Sélectionnez "Tout effacer"
3. Cliquez sur "Effacer les données"

#### Firefox :
1. Appuyez sur **Ctrl + Shift + Delete**
2. Sélectionnez "Tout"
3. Cliquez sur "Effacer maintenant"

### Solution 2: Rechargement Forcé

- **Ctrl + F5** (rechargement forcé)
- **Ctrl + Shift + R** (rechargement sans cache)

### Solution 3: Utiliser une URL Différente

Au lieu de `127.0.0.1:8000`, utilisez :
- `http://localhost:8000` ✅ (recommandé)
- `http://0.0.0.0:8000`

### Solution 4: Mode Navigation Privée

1. Ouvrez une **fenêtre de navigation privée**
2. Accédez à `http://localhost:8000`
3. Cela évite le cache et l'historique

### Solution 5: Scripts de Lancement

Utilisez les nouveaux scripts créés :

```bash
# Python
python run_dev_http.py

# Windows
run_dev_http.bat
```

Ces scripts utilisent `0.0.0.0:8000` pour éviter les problèmes de cache.

## Vérification

Pour vérifier que le serveur fonctionne en HTTP :

1. **Lancez le serveur** avec `python run_dev_http.py`
2. **Ouvrez** `http://localhost:8000` dans votre navigateur
3. **Vérifiez** qu'il n'y a pas d'erreur SSL
4. **Vérifiez** que l'URL commence par `http://` et non `https://`

## Prévention

Pour éviter ce problème à l'avenir :

1. **Toujours utiliser** `http://localhost:8000` en développement
2. **Ne jamais utiliser** `https://` avec le serveur de développement Django
3. **Vider le cache** régulièrement si vous changez de configuration
4. **Utiliser les scripts** fournis pour lancer le serveur

## Commandes Utiles

```bash
# Lancer avec localhost (recommandé)
python run_dev_http.py

# Lancer avec 127.0.0.1
python manage.py runserver localhost:8000

# Lancer avec 0.0.0.0 (toutes interfaces)
python manage.py runserver 0.0.0.0:8000
```

## URLs Correctes

✅ **Utilisez ces URLs :**
- `http://localhost:8000`
- `http://127.0.0.1:8000`
- `http://0.0.0.0:8000`

❌ **N'utilisez PAS ces URLs :**
- `https://localhost:8000`
- `https://127.0.0.1:8000`
- `https://0.0.0.0:8000`
