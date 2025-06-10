# 💻 calServer Labeltool

[![Build Windows Electron App](https://github.com/bastelix/calServer-print/actions/workflows/build-windows.yml/badge.svg)](https://github.com/bastelix/calServer-print/actions/workflows/build-windows.yml)
[![Tests](https://github.com/bastelix/calServer-print/actions/workflows/tests.yml/badge.svg)](https://github.com/bastelix/calServer-print/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/bastelix/calServer-print?label=release)](https://github.com/bastelix/calServer-print/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

calServer Labeltool ist ein kleines Werkzeug zum Erstellen von Geraete- und Kalibrierungsetiketten mit QR-Codes. Die benoetigten Daten werden ueber eine calServer-API abgerufen und die erzeugten Labels koennen direkt im Browser oder ueber die mitgelieferte Desktop-Anwendung gedruckt werden.

## Projektumfang und Idee

Ziel des Projektes ist es, das Erstellen von Kalibrierungs- und Geraetebeschriftungen zu vereinfachen. Die Anwendung besteht aus einem NiceGUI-Webinterface und kann mit Electron zu einer Desktop-App gebuendelt werden. Sie kommuniziert mit einem bestehenden **calServer**-Backend, um die noetigen Informationen abzurufen und daraus Etiketten mit QR-Codes zu erzeugen.

## Features

- Abruf von Kalibrierdaten ueber eine REST-API
- Darstellung als **Geraete-** oder **Kalibrierungsetikett**
- Generierung von QR-Codes
- Ausgabe auf beliebigen lokalen Druckern
- Optionale Nutzung als Electron-Desktop-Anwendung
- Ausführliches Logfenster zur Fehlerdiagnose
- Temporäres Speichern der eingegebenen Login-Daten

## Installation

1. Repository klonen:
   ```bash
   git clone <REPO-URL>
   cd calServer-print
   ```
2. Python-Abhaengigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Node-Umgebung fuer die Desktop-Version einrichten:
   ```bash
   cd electron
   npm install
   cd ..
   ```
   Node.js muss installiert sein, damit `npm` verfuegbar ist. Fehlt `npm`,
   laesst sich Node.js ueber <https://nodejs.org/> oder per
   `winget install OpenJS.NodeJS.LTS` nachinstallieren.
   > **Hinweis:** Falls npm den Fehler `ENOENT` meldet, wird das Kommando meist
   > im falschen Verzeichnis ausgefuehrt. Stelle sicher, dass du dich im
   > `electron`-Ordner befindest oder dort eine `package.json` mit
   > `npm init -y` erzeugst.

4. Alternativ koennen alle Abhaengigkeiten in einem Schritt installiert
   werden:
   ```bash
   ./setup.sh
   ```
5. Windows-Nutzer koennen stattdessen die WinGet-Konfiguration nutzen,
   um Python, Node.js, Visual Studio Code und saemtliche
   Projektabhaengigkeiten automatisch einzurichten:
   ```powershell
   winget configure --file install-windows.yaml
   ```

## ⚡ Lokaler Start (NiceGUI)

```bash
python -m app.main
# or
python run.py
```

Das Webinterface ist danach unter `http://localhost:8080` erreichbar.

Wenn die Umgebungsvariable `APP_ENV` auf `development` gesetzt ist,
werden die Login-Felder mit Demo-Zugangsdaten vorbefüllt. Ein Beispiel
hierzu findet sich in `.env.example`, welches zudem den Eintrag
`DOMAIN=demo.net-cal.com` für die Demo-API enthält. Liegt eine `.env`
Datei im Projektverzeichnis, wird sie beim Start über `launcher.py`
automatisch mit **python-dotenv** eingelesen. Darin kann z.B. ein Pfad
für `APP_CONFIG` gesetzt werden.

## ⚡ Start als Desktop-App

Im `electron`-Verzeichnis befinden sich die Dateien fuer die Electron-Anwendung. Nach der Installation der Node-Abhaengigkeiten laesst sich die App mit

```bash
npm start
```

im Fenstermodus ausfuehren.

## 🐳 Docker Compose

Für den produktiven Einsatz liegt ein einfaches Docker‑Compose Setup bei.
Damit lässt sich die Anwendung zusammen mit einem Nginx‑Reverse‑Proxy und
automatisch erneuerten Let's‑Encrypt Zertifikaten starten.

1. `.env.example` kopieren und die Werte für `DOMAIN` und
   `LETSENCRYPT_EMAIL` anpassen:

   ```bash
   cp .env.example .env
   # DOMAIN=my.example.com
   # LETSENCRYPT_EMAIL=admin@my.example.com
   # optional: APP_ENV=development
   # optional: APP_CONFIG=/path/to/config.json
   ```

2. Danach das Setup starten:

   ```bash
   docker-compose up -d
   ```

   Die Anwendung ist anschließend unter `https://<DOMAIN>` erreichbar.
   Alle Variablen aus der `.env` Datei werden beim Start in den Container
   übernommen und stehen der Anwendung zur Verfügung.

## ♻ Release Build

Die Release-Pakete basieren auf einer gebuendelten Python/NiceGUI-Exe.
Zum Verpacken wird das kleine Startskript (`launcher.py`) genutzt,
welches NiceGUI im Headless-Modus startet. Dieses wird zunaechst mit
PyInstaller erzeugt:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --noconsole --name labeltool --add-data "app;app" launcher.py
```

Damit entsteht `dist/labeltool.exe`, das anschliessend in den Electron-Build uebernommen wird.

```bash
npm run build
```

Der Befehl erzeugt im Ordner `release/` Installationspakete fuer Windows, Linux und macOS. Beim Pushen eines Tags in der Form `v1.0.0` wird dieser Schritt automatisch in GitHub Actions ausgefuehrt.

### Signieren und ZIP-Installer (Windows)

Um die erzeugte `labeltool.exe` lokal ohne Warnmeldungen ausfuehren zu koennen,
kann sie mit einem selbstsignierten Zertifikat signiert werden. Die folgenden
Befehle werden in einer PowerShell ausgefuehrt:

```powershell
# Selbstsigniertes Codesign-Zertifikat erstellen
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Test Cert" -CertStoreLocation "cert:\CurrentUser\My"
# Zertifikat als PFX exportieren (Thumbprint anpassen)
Export-PfxCertificate -Cert "cert:\CurrentUser\My\$($cert.Thumbprint)" -FilePath cert\selfsign.pfx -Password (ConvertTo-SecureString -String "testpass" -Force -AsPlainText)

# Signieren und ZIP erstellen
./build-installer.ps1
```

Das Skript `build-installer.ps1` erzeugt (falls noetig) mit PyInstaller die
Datei `dist/labeltool.exe` und signiert sie mit dem zuvor erzeugten
Zertifikat. Diese EXE wird spaeter vom Electron-Build (siehe Workflow
"Build Windows Electron App") in das portable Paket integriert. Zudem legt
das Skript ein einfaches ZIP `dist/labeltool.zip` mit der signierten Datei
an.

## Schritt-fuer-Schritt-Anleitung zum Testen

1. **Server vorbereiten:** Stelle sicher, dass ein calServer mit gueltigen API-Zugangsdaten laeuft oder verwende Testendpunkte.
2. **Applikation starten:** Entweder lokal mit `python app/main.py` oder als Electron-App mit `npm start`.
3. **Weboberflaeche oeffnen:** Browser oeffnen und `http://localhost:8080` aufrufen (bei der Desktop-App oeffnet sich automatisch ein Fenster).
4. **Zugangsdaten eingeben:** API-Basis-URL, Benutzername, Passwort und API-Key ausfuellen. Optional kann ein JSON-Filter angegeben werden, um bestimmte Daten zu laden.
5. **Labeltyp waehlen:** Zwischen "Device" und "Calibration" entscheiden.
6. **Daten abrufen:** Button **Fetch Data** betaetigen. Bei Erfolg erscheinen die geladenen Daten.
7. **Label anzeigen und Drucker auswaehlen:** Das generierte Etikett wird dargestellt, darunter laesst sich aus der Liste der erkannten Drucker einer auswaehlen.
8. **Drucken:** Mit **Print** wird das Label an den ausgewaehlten Drucker geschickt.

Damit laesst sich der komplette Ablauf von der Datenerfassung bis zum fertigen Etikett nachvollziehen.

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
Releases werden ausserdem automatisch erzeugt, sobald ein Tag (`v1.0.0`) gepusht wird.

## 🧪 Tests ausfuehren

Fuer die Test-Suite kommt `pytest` zum Einsatz. Nach der Installation der
Python-Abhaengigkeiten lassen sich die Tests wie folgt starten:

```bash
pytest
```
