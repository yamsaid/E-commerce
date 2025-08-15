# Guide de Dépannage - Erreurs Render

## Erreur "Internal Server Error"

Si vous obtenez une erreur "Internal Server Error" après le déploiement sur Render, suivez ces étapes de diagnostic :

### 1. Vérifier les Logs Render

1. Allez sur votre dashboard Render
2. Cliquez sur votre service web
3. Allez dans l'onglet "Logs"
4. Cherchez les erreurs récentes

### 2. Problèmes Courants et Solutions

#### A. Problème de SECRET_KEY

**Symptôme :** Erreur liée à SECRET_KEY dans les logs

**Solution :**
- Render génère automatiquement une SECRET_KEY
- Vérifiez qu'elle est bien configurée dans les variables d'environnement
- Si manquante, ajoutez-la manuellement dans Render

#### B. Problème de Base de Données

**Symptôme :** Erreur de connexion PostgreSQL

**Solutions :**
1. **Vérifier que la base de données est créée :**
   - Allez dans l'onglet "Environment" de votre service
   - Vérifiez que `DATABASE_URL` est présent

2. **Vérifier les migrations :**
   - Les migrations doivent s'exécuter automatiquement
   - Si échec, vérifiez les logs de build

3. **Base de données non créée :**
   - Vérifiez que le service de base de données est bien créé
   - Le nom doit correspondre à `novalearnweb-db` dans `render.yaml`

#### C. Problème de Dépendances

**Symptôme :** Erreur d'import de modules

**Solutions :**
1. **Vérifier requirements.txt :**
   ```bash
   psycopg==3.1.18
   dj-database-url==2.1.0
   ```

2. **Vérifier le script de build :**
   - Le script `build.sh` doit s'exécuter sans erreur
   - Vérifiez les logs de build

#### D. Problème de Variables d'Environnement

**Symptôme :** Configuration manquante

**Variables requises :**
```bash
DJANGO_SETTINGS_MODULE=novalearnweb.production
SECRET_KEY=<généré automatiquement>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
DATABASE_URL=<généré automatiquement>
```

### 3. Diagnostic Local

Testez votre configuration localement :

```bash
# Test de la configuration de production
python test_production.py

# Test avec les variables d'environnement
set DJANGO_SETTINGS_MODULE=novalearnweb.production
set DEBUG=False
python manage.py check --deploy
```

### 4. Solutions de Contournement

#### A. Utiliser SQLite temporairement

Si PostgreSQL pose problème, modifiez temporairement `render.yaml` :

```yaml
envVars:
  - key: DJANGO_SETTINGS_MODULE
    value: novalearnweb.development  # Utilise SQLite
```

#### B. Activer DEBUG temporairement

Pour voir les erreurs détaillées :

```yaml
envVars:
  - key: DEBUG
    value: True
```

**⚠️ N'oubliez pas de remettre `False` après diagnostic !**

### 5. Vérification Post-Déploiement

Après un déploiement réussi :

1. **Vérifier l'URL de l'application**
2. **Tester les fonctionnalités principales**
3. **Vérifier les logs pour les erreurs**
4. **Tester la base de données**

### 6. Commandes Utiles

```bash
# Vérifier la configuration
python manage.py check --deploy

# Tester les migrations
python manage.py migrate --plan

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Créer un superutilisateur
python manage.py createsuperuser
```

### 7. Contact Support

Si les problèmes persistent :

1. **Collectez les logs complets**
2. **Notez les étapes de reproduction**
3. **Vérifiez la configuration Render**
4. **Contactez le support Render si nécessaire**

### 8. Prévention

Pour éviter les problèmes futurs :

1. **Testez localement avant déploiement**
2. **Utilisez des variables d'environnement**
3. **Vérifiez les logs régulièrement**
4. **Maintenez les dépendances à jour**
