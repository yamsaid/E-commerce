@echo off
echo 🚀 Démarrage du serveur Django en mode développement...
echo 📍 URL: http://localhost:8000 (recommandé)
echo 📍 URL: http://127.0.0.1:8000
echo 📍 URL: http://0.0.0.0:8000
echo 🔧 Mode: DEBUG=True, HTTPS désactivé
echo ⚠️  IMPORTANT: Utilisez HTTP, pas HTTPS!
echo ============================================================
python run_dev_http.py
pause
