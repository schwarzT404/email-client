@echo off
chcp 65001 >nul
title 🚀 Système Support Client E-commerce - Claude 4

echo.
echo 🚀 SYSTÈME SUPPORT CLIENT E-COMMERCE
echo =====================================
echo.
echo 🤖 Propulsé par Claude 4
echo 📧 Automatisation complète
echo 🌐 Interface web + Admin
echo.

:: Vérifier si on est dans le bon répertoire
if not exist "web_app\app.py" (
    echo ❌ Erreur: Fichiers système non trouvés
    echo 💡 Assurez-vous d'être dans le bon répertoire
    pause
    exit /b 1
)

:: Vérifier l'environnement virtuel
if not defined VIRTUAL_ENV (
    echo 🔄 Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ❌ Erreur activation environnement virtuel
        echo 💡 Exécutez: python -m venv venv
        pause
        exit /b 1
    )
)

echo ✅ Environnement virtuel actif
echo.

:: Menu de choix
echo 🎯 CHOISISSEZ VOTRE ACTION :
echo    1. 🛠️  Réparer + Lancer système complet
echo    2. 🌐 Lancer seulement l'application web  
echo    3. 👑 Lancer seulement l'interface admin
echo    4. 🤖 Lancer le bot de simulation
echo    5. ✨ Démonstration spectaculaire
echo    6. 🔧 Réparation d'urgence uniquement
echo.

set /p choix="Votre choix (1-6) : "

if "%choix%"=="1" goto :complet
if "%choix%"=="2" goto :webapp
if "%choix%"=="3" goto :admin
if "%choix%"=="4" goto :bot
if "%choix%"=="5" goto :demo
if "%choix%"=="6" goto :reparation
goto :erreur

:complet
echo.
echo 🛠️  RÉPARATION + LANCEMENT COMPLET
echo ===================================
echo.
echo 🔧 Réparation de la base de données...
python reparation_urgente.py
if errorlevel 1 (
    echo ❌ Erreur lors de la réparation
    pause
    exit /b 1
)

echo.
echo 🚀 Lancement du système complet...
python lancer_systeme_complet.py
goto :fin

:webapp
echo.
echo 🌐 LANCEMENT APPLICATION WEB
echo ============================
echo.
cd web_app
echo 🚀 Démarrage sur http://localhost:5000...
start http://localhost:5000
python app.py
cd ..
goto :fin

:admin
echo.
echo 👑 LANCEMENT INTERFACE ADMIN
echo =============================
echo.
echo 🚀 Démarrage sur http://localhost:5001...
start http://localhost:5001
python admin_interface.py
goto :fin

:bot
echo.
echo 🤖 LANCEMENT BOT DE SIMULATION
echo ===============================
echo.
python bot_simulation_emails.py
goto :fin

:demo
echo.
echo ✨ DÉMONSTRATION SPECTACULAIRE
echo ===============================
echo.
python demo_spectaculaire.py
goto :fin

:reparation
echo.
echo 🔧 RÉPARATION D'URGENCE
echo =======================
echo.
python reparation_urgente.py
echo.
echo ✅ Réparation terminée !
pause
goto :fin

:erreur
echo ❌ Choix invalide
pause
goto :fin

:fin
echo.
echo 🎉 Merci d'avoir utilisé notre système !
pause 