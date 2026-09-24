# PSA-Track – Einsatz- & Hygiene-Management
PSA-Track ist eine schlanke Windows-Anwendung zur Erfassung und Protokollierung von Persönlicher Schutzausrüstung (PSA) bei Einsätzen und Übungen. Die Software unterstützt die Schwarz/Weiß-Trennung (Einsatzstellenhygiene), um kontaminierte Ausrüstung direkt vor Ort zu dokumentieren und Tauschausrüstung zuzuordnen.

🚀 Schnellstart & Download
> Keine Python-Installation oder Einrichtung erforderlich.

Lade die fertige psa_track.exe hier aus dem Repository herunter (oder unter Releases). Starte die Datei direkt per Doppelklick. Beim ersten Start wird im selben Ordner automatisch die lokale Datenbank psa_track.db angelegt.

🎯 Kernfunktionen
> Touch-optimierte Oberfläche: Große Schaltflächen und klare Kontraste für die Bedienung auf Tablets, Touchscreens oder Toughbooks (auch mit Handschuhen).

> Schneller Scan-Workflow

> Einsatzmodus: Erfassung je Kamerad oder Trupp. Barcode-Scans buchen Ausrüstung direkt als NEU (Ausgabe) oder ALT (Abgabe/Kontaminiert).

> Automatische Trägerzuordnung: Kontaminierte Kleidung wird aus der Personenliste ausgebucht und auf den Status Kontaminiert gesetzt.

> Wache-Modus: Übersicht über den aktuellen Ausrüstungsbestand und chronologisches Gesamtprotokoll aller Buchungen.

> Fehlertolerant & Sicher:

> Dialoge zur Bestätigung vor dem Löschen von Datensätzen.

> Beim Umbenennen von Personen oder Trupps bleibt die historische Datenintegrität in der Datenbank erhalten.

💻 Hinweise für IT-Administratoren
> Architektur: Portable Windows-Anwendung auf Python- und CustomTkinter-Basis mit lokaler SQLite3-Datenbank.

> Keine Cloud / Kein Server: Die Anwendung arbeitet vollständig offline und benötigt keine Server-Infrastruktur oder Datenbank-Dienste.

> Deployment / Dateisystem:

> Die psa_track.exe ist portable und benötigt keine Administratorrechte zur Ausführung.

> Die Datenbank (psa_track.db) wird zur Laufzeit im selben Verzeichnis wie die .exe geschrieben.

> Sicherung: Für Backups reicht es aus, die Datei psa_track.db zu sichern oder das gesamte Verzeichnis zu kopieren.

📦 Verwendete Bibliotheken & Danksagung
CustomTkinter (MIT Lizenz) – Modernes UI-Framework auf Tkinter-Basis von Tom Schimansky.

Python Standalone Library (sqlite3) – Integrierte SQL-Datenbank-Engine.

PyInstaller (GPLv2/Loggerhead) – Deployment-Tooling zur Erstellung der Standalone-Executable.

📜 Lizenz
Dieses Projekt ist unter der GNU General Public License v3.0 (GPLv3) lizenziert. Weitere Details befinden sich in der LICENSE-Datei.

🛠️ Für Entwickler: Aus Quellcode ausführen & Bauen
(Nur relevant, wenn du Änderungen am Quellcode vornehmen möchtest)

Voraussetzungen
Python 3.8+ sowie customtkinter:

Bash
pip install customtkinter
Anwendung über Quellcode starten
Bash
python psa_track.py
Eigene EXE-Datei bauen (PyInstaller)
Falls du den Code angepasst hast und eine neue .exe erstellen möchtest:

Bash
python -m pip install pyinstaller
python -m PyInstaller --noconsole --onefile --collect-all customtkinter psa_track.py
