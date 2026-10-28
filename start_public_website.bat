@echo off
title SRMIST AI Duplicate Detector - Public Web Server
echo ======================================================================
echo   SRM INSTITUTE OF SCIENCE AND TECHNOLOGY - DEPARTMENT OF AI
echo   AI Project Idea Duplicate Detector & Entity Resolution System
echo   Guide: Dr. S.P. Ramya
echo   Team: Sudhan Babu, Keerthi Vasaa, Dayanandan
echo ======================================================================
echo.
echo [*] Initializing SQL Database and Vector Embeddings...
python seed_data.py
echo.
echo [*] Launching Python Flask Web Server (Port 5000)...
start "Flask Server" python run.py
timeout /t 2 >nul
echo.
echo [*] Launching Public Internet Cloudflare Tunnel...
start "Cloudflare Public Tunnel" .\cloudflared.exe tunnel --url http://127.0.0.1:5000
echo.
echo ======================================================================
echo [+] YOUR WEBSITE IS NOW LIVE ON THE PUBLIC INTERNET:
echo     URL: https://supplemental-combinations-hollow-competing.trycloudflare.com
echo.
echo [+] ACADEMIC REVIEW CREDENTIALS:
echo     - Faculty Guide: username: ramya.guide   ^| password: password123
echo     - Lead Student:  username: sudhan        ^| password: password123
echo ======================================================================
pause
