# 💻 calServer Labeltool

calServer Labeltool is a small tool for generating device and calibration labels that include QR codes. It fetches data from a calServer API and allows printing the resulting labels directly from the browser or via the packaged desktop application.

## Projektumfang und Idee

Ziel des Projektes ist es, das Erstellen von Kalibrierungs- und Geraetebeschriftungen zu vereinfachen. Die Anwendung besteht aus einem Streamlit-Webinterface und kann mit Electron zu einer Desktop-App gebuendelt werden. Sie kommuniziert mit einem bestehenden **calServer**-Backend, um die noetigen Informationen abzurufen und daraus Etiketten mit QR-Codes zu erzeugen.

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

## ⚡ Lokaler Start (Streamlit)

```bash
streamlit run app/main.py
```

Das Webinterface ist danach unter `http://localhost:8501` erreichbar.

## ⚡ Start als Desktop-App

Im `electron`-Verzeichnis befinden sich die Dateien fuer die Electron-Anwendung. Nach der Installation der Node-Abhaengigkeiten laesst sich die App mit

```bash
npm start
```

im Fenstermodus ausfuehren.

## ♻ Release Build

```bash
npm run build
```

Der Befehl erzeugt im Ordner `release/` Installationspakete fuer Windows, Linux und macOS. Beim Pushen eines Tags in der Form `v1.0.0` wird dieser Schritt automatisch in GitHub Actions ausgefuehrt.

## Schritt-fuer-Schritt-Anleitung zum Testen

1. **Server vorbereiten:** Stelle sicher, dass ein calServer mit gueltigen API-Zugangsdaten laeuft oder verwende Testendpunkte.
2. **Applikation starten:** Entweder lokal mit `streamlit run app/main.py` oder als Electron-App mit `npm start`.
3. **Weboberflaeche oeffnen:** Browser oeffnen und `http://localhost:8501` aufrufen (bei der Desktop-App oeffnet sich automatisch ein Fenster).
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
