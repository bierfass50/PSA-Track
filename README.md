# 🚒 PSA-Track

> **Digitales Einsatz- & Hygiene-Management für Feuerwehren**

[![Lizenz: GPLv3](https://img.shields.io/badge/Lizenz-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Plattform-Windows-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-informational.svg)]()

**PSA-Track** ist eine schlanke, touch-optimierte Windows-Anwendung zur Erfassung und Protokollierung von Persönlicher Schutzausrüstung (PSA) bei Einsätzen und Übungen. Die Software unterstützt die konsequente **Schwarz/Weiß-Trennung** (Einsatzstellenhygiene), um kontaminierte Ausrüstung direkt vor Ort zu dokumentieren und Tauschausrüstung zuzuordnen.

## 📜 Lizenz & Nutzung (Auf einen Blick)

**PSA-Track** ist als **Open-Source-Software** unter der **GNU General Public License v3.0 (GPLv3)** lizenziert.

Für Anwender, Kommandanten und Verwaltungen bedeutet das konkret:

* 🆓 **100% Kostenlos:** Es gibt keine Lizenzgebühren, Abos, Testphasen oder versteckten Kosten.
* 🚒 **Unbeschränkte Nutzung:** Jede Feuerwehr, Hilfsorganisation (THW, DRK, etc.), Kommune oder Firma darf die Software auf beliebig vielen Geräten installieren und dauerhaft nutzen.
* 🔓 **Offener Quellcode:** Jeder darf den Code einsehen, anpassen und verbessern. Einzige Regel: Wer Anpassungen veröffentlicht, muss auch diesen Code wieder unter der GPLv3 frei zur Verfügung stellen.
* 🛡️ **Haftungsausschluss:** Die Bereitstellung erfolgt wie besehen (*"AS IS"*) auf eigener Verantwortung. Es wird keine Gewährleistung oder kommerzielle Haftung übernommen.

---

## 🚀 Schnellstart & Download

> [!TIP]
> **Keine Python-Installation oder Einrichtung erforderlich!**

1. Lade die aktuelle `psa_track.exe` aus dem Repository *(oder unter Releases)* herunter.
2. Starte die Datei direkt per Doppelklick.
3. Beim ersten Start wird die lokale Datenbank `psa_track.db` automatisch im selben Ordner erstellt.

---

## 📋 Kernfunktionen

* **📱 Touch & Tablet-Ready**  
  Große Buttons und klare Kontraste – ideal für die Bedienung auf Tablets, Touchscreens oder Toughbooks (auch mit Einsatzhandschuhen).

* **⚡ Schneller Scan-Workflow**  
  * **Einsatzmodus:** Erfassung je Kamerad oder Trupp. Barcode-Scans buchen Ausrüstung direkt als **NEU (Ausgabe)** oder **ALT (Abgabe/Kontaminiert)**.
  * **Automatische Trägerzuordnung:** Kontaminierte Kleidung wird aus der Personenliste ausgebucht und auf den Status *Kontaminiert* gesetzt.

* **🏛️ Wache-Modus**  
  Übersicht über den aktuellen Gesamtausrüstungs-Bestand und chronologisches Protokoll aller Buchungen.

* **🛡️ Fehlertolerant & Datensicher**  
  * Bestätigungsdialoge vor dem Löschen von Daten.
  * Namensänderungen von Personen oder Trupps bleiben in der Historie vollständig erhalten.

---

## 🖥️ Hinweise für IT-Administratoren

> [!NOTE]
> **Standalone & Offline-fähig**  
> PSA-Track benötigt keine Server-Infrastruktur, keine Datenbank-Dienste und keine Internetverbindung.

| Eigenschaft | Details |
| :--- | :--- |
| **Architektur** | Portable Windows-Anwendung (Python / CustomTkinter / SQLite3) |
| **Rechte** | Benötigt **keine** Administratorrechte |
| **Speicherort** | Datenbank (`psa_track.db`) liegt lokal im Anwendungsverzeichnis |
| **Backup** | Einfache Sicherung durch Kopieren der `psa_track.db` |

---

## 📦 Verwendete Bibliotheken & Danksagung

* **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** (MIT Lizenz) – Modernes UI-Framework auf Tkinter-Basis von Tom Schimansky.
* **[sqlite3](https://docs.python.org/3/library/sqlite3.html)** – Integrierte Python-Datenbank-Engine.
* **[PyInstaller](https://pyinstaller.org/)** (GPLv2 mit Bootloader Exception) – Deployment-Tooling zur Erstellung der Standalone-EXE.

---

## 📜 Lizenz

Dieses Projekt ist unter der **GNU General Public License v3.0 (GPLv3)** lizenziert. Weitere Details befinden sich in der `LICENSE`-Datei.

---

## 🛠️ Für Entwickler: Aus Quellcode ausführen & Bauen

*(Nur relevant, wenn du Änderungen am Quellcode vornehmen möchtest)*

### 1. Voraussetzungen
Python 3.8+ installieren und Abhängigkeiten laden:
```bash
pip install customtkinter
```

### 2. Anwendung über Quellcode starten
```bash
python psa_track.py
```

### 3. Eigene EXE-Datei erstellen (PyInstaller)
Falls du den Code angepasst hast und eine neue `.exe` erstellen möchtest:
```bash
python -m pip install pyinstaller
python -m PyInstaller --noconsole --onefile --collect-all customtkinter psa_track.py
```
Die fertige Executable wird im Ordner `dist/` abgelegt.
