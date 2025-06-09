# 💻 calServer Labeltool

[![Build Windows Electron App](https://github.com/bastelix/calServer-print/actions/workflows/build-windows.yml/badge.svg)](https://github.com/bastelix/calServer-print/actions/workflows/build-windows.yml)
[![Tests](https://github.com/bastelix/calServer-print/actions/workflows/tests.yml/badge.svg)](https://github.com/bastelix/calServer-print/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

calServer Labeltool is a small tool for generating device and calibration labels that include QR codes. It fetches data from a calServer API and allows printing the resulting labels directly from the browser or via the packaged desktop application.

## Projektumfang und Idee

Ziel des Projektes ist es, das Erstellen von Kalibrierungs- und Geraetebeschriftungen zu vereinfachen. Die Anwendung besteht aus einem NiceGUI-Webinterface und kann mit Electron zu einer Desktop-App gebuendelt werden. Sie kommuniziert mit einem bestehenden **calServer**-Backend, um die noetigen Informationen abzurufen und daraus Etiketten mit QR-Codes zu erzeugen.

## Features

- Abruf von Kalibrierdaten ueber eine REST-API
- Darstellung als **Geraete-** oder **Kalibrierungsetikett**
- Generierung von QR-Codes
- Ausgabe auf beliebigen lokalen Druckern
- Optionale Nutzung als Electron-Desktop-Anwendung

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
   > **Hinweis:** Falls npm den Fehler `ENOENT` meldet, wird das Kommando meist
   > im falschen Verzeichnis ausgefuehrt. Stelle sicher, dass du dich im
   > `electron`-Ordner befindest oder dort eine `package.json` mit
   > `npm init -y` erzeugst.

4. Alternativ koennen alle Abhaengigkeiten in einem Schritt installiert
   werden:
   ```bash
   ./setup.sh
   ```

## ⚡ Lokaler Start (NiceGUI)

```bash
python app/main.py
# or
python launcher.py
```

Das Webinterface ist danach unter `http://localhost:8080` erreichbar.

## ⚡ Start als Desktop-App

Im `electron`-Verzeichnis befinden sich die Dateien fuer die Electron-Anwendung. Nach der Installation der Node-Abhaengigkeiten laesst sich die App mit

```bash
npm start
```

im Fenstermodus ausfuehren.

## ♻ Release Build

The release packages depend on a bundled Python/NiceGUI executable. For
packaging a small launcher script (`launcher.py`) is used to start NiceGUI in
headless mode. Build it first using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --name labeltool --add-data "app;app" launcher.py
```

This creates `dist/labeltool.exe` which will be included in the Electron build.

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

Das Skript `build-installer.ps1` signiert die Datei `dist/labeltool.exe` mit dem
vorher erzeugten Zertifikat und legt anschliessend `dist/labeltool.zip` als
portables Paket an.

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
Releases are also created automatically when pushing a tag (`v1.0.0`).

## 🧪 Running Tests

The project uses `pytest` for its test-suite. After installing the Python
dependencies you can execute the tests via:

```bash
pytest
```
