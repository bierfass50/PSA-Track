# ==============================================================================
# PSA-Track - Digitales Einsatz- & Hygiene-Management
# Copyright (C) 2026 Leander Dammenhayn
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License v3 for more details.
# ==============================================================================

import os
import sys
import sqlite3
import random
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# ReportLab für professionelle PDF-Exporte mit Unterschriftenfeld
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Globaler Absturz-Schutz (Catch-All Exception Handler)
def global_exception_handler(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print("EINSATZ-FEHLER ABGEFANGEN:\n", error_msg)
    try:
        messagebox.showerror(
            "System-Hinweis", 
            f"Ein unerwarteter Fehler wurde abgefangen:\n{value}\n\nDas Programm läuft stabil weiter."
        )
    except Exception:
        pass

sys.excepthook = global_exception_handler

# CustomTkinter Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FlackerfreiesModal(ctk.CTkToplevel):
    """Spezialfenster, das erst nach vollständiger Berechnung eingeblendet wird."""
    def __init__(self, parent, title="Dialog", width=420, height=200):
        super().__init__(parent)
        self.withdraw()  # Verstecken gegen weißes Aufblitzen
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.deiconify()


class PSATrackApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PSA-Track - Digitales Einsatz- & Hygiene-Management")
        self.geometry("1280x760")
        self.minsize(1024, 640)

        self.init_db()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top Bar (dynamischer Hintergrund je nach Modus)
        self.top_bar = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#0F172A")
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # Titel & Modus-Indikator
        self.title_label = ctk.CTkLabel(
            self.top_bar, 
            text="🚨 EINSATZMODUS AKTIV", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(side="left", padx=20)

        # Sub-Titel / System-Tag
        self.sub_title_label = ctk.CTkLabel(
            self.top_bar,
            text="PSA-Track Hygiene-Erfassung",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.sub_title_label.pack(side="left", padx=(0, 20))

        # Modus-Schalter
        self.mode_segmented = ctk.CTkSegmentedButton(
            self.top_bar,
            values=["Einsatzmodus", "Wache-Modus"],
            command=self.switch_mode,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42,
            selected_color="#DC2626",
            selected_hover_color="#B91C1C"
        )
        self.mode_segmented.pack(side="right", padx=15, pady=14)

        # DB-Löschen Button (Standardmäßig versteckt, nur im Wache-Modus sichtbar)
        self.btn_db_reset = ctk.CTkButton(
            self.top_bar,
            text="🗑️ DB löschen",
            command=self.prompt_easter_egg_delete,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7F1D1D", hover_color="#991B1B",
            width=110, height=36
        )

        # Haupt-Container
        self.einsatz_frame = ctk.CTkFrame(self, corner_radius=0)
        self.wache_frame = ctk.CTkFrame(self, corner_radius=0)

        self.setup_einsatz_modus()
        self.setup_wache_modus()

        # Start im Einsatzmodus
        self.mode_segmented.set("Einsatzmodus")
        self.switch_mode("Einsatzmodus")

    def init_db(self):
        """SQLite mit WAL-Modus für maximale Schreib-Performance & Ausfallsicherheit."""
        self.conn = sqlite3.connect("psa_track.db", timeout=10.0)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.cursor.execute("PRAGMA synchronous=NORMAL;")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ausruestung (
                inv_nr TEXT PRIMARY KEY,
                bezeichnung TEXT,
                status TEXT,
                traeger TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS protokoll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zeitstempel TEXT,
                person TEXT,
                inv_nr TEXT,
                aktion TEXT
            )
        """)
        self.conn.commit()

        # Stammdaten-Initialisierung falls leer
        self.cursor.execute("SELECT COUNT(*) FROM ausruestung")
        if self.cursor.fetchone()[0] == 0:
            sample_data = [
                ("J-101", "Einsatzjacke S-Gard", "Weiß", "Frei"),
                ("J-102", "Einsatzjacke S-Gard", "Weiß", "Frei"),
                ("H-201", "Einsatzhose S-Gard", "Weiß", "Frei"),
                ("M-301", "PA-Maske Ultraflow", "Weiß", "Frei"),
            ]
            self.cursor.executemany("INSERT INTO ausruestung VALUES (?, ?, ?, ?)", sample_data)
            self.conn.commit()

    def switch_mode(self, mode):
        if mode == "Einsatzmodus":
            # Optische Anpassungen für Einsatzmodus (Feuerwehr-Rot Akzent, auffällig aber nicht grell)
            self.top_bar.configure(fg_color="#7F1D1D")  # Sattes Dunkelrot
            self.title_label.configure(text="🚨 EINSATZMODUS AKTIV", text_color="#FFFFFF")
            self.sub_title_label.configure(text="Schnell-Erfassung & Atemschutz-Hygiene", text_color="#FECACA")
            self.mode_segmented.configure(selected_color="#DC2626", selected_hover_color="#B91C1C")

            self.btn_db_reset.pack_forget()  # Im Einsatzmodus VERSTECKEN
            self.wache_frame.grid_forget()
            self.einsatz_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        else:
            # Optische Anpassungen für Wache-Modus (Klassisches Navy/Slate-Dunkelblau)
            self.top_bar.configure(fg_color="#0F172A")  # Ruhiges Dunkelblau
            self.title_label.configure(text="🚒 PSA-Track | Wache-Modus", text_color="#F8FAFC")
            self.sub_title_label.configure(text="Bestandsverwaltung & Protokoll-Exporte", text_color="#94A3B8")
            self.mode_segmented.configure(selected_color="#2563EB", selected_hover_color="#1D4ED8")

            self.einsatz_frame.grid_forget()
            self.refresh_wache_view()
            self.wache_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
            # Im Wache-Modus ANZEIGEN
            self.btn_db_reset.pack(side="right", padx=(5, 10), pady=14)

    # --- EASTER EGG: DATENBANK LÖSCHEN DIALOG ---
    def prompt_easter_egg_delete(self):
        modal = FlackerfreiesModal(self, title="⚠️ Datenbank wirklich zurücksetzen?", width=480, height=340)

        # Header Info
        header_frame = ctk.CTkFrame(modal, fg_color="#1E293B", corner_radius=8)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        lbl_title = ctk.CTkLabel(
            header_frame, 
            text="⚠️ ACHTUNG: VOLLSTÄNDIGE LÖSCHUNG", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FCA5A5"
        )
        lbl_title.pack(pady=(10, 2))

        lbl_desc = ctk.CTkLabel(
            header_frame, 
            text="Möchtest du die gesamte Datenbank leeren?\nAlle Protokolle & Ausrüstungen werden unwiderruflich gelöscht.", 
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1"
        )
        lbl_desc.pack(pady=(0, 10))

        # Springendes Spielfeld
        play_area = ctk.CTkFrame(modal, fg_color="#0F172A", corner_radius=8, width=450, height=140)
        play_area.pack(padx=15, pady=5)
        play_area.pack_propagate(False)

        click_count = 0

        def jump_button():
            max_x = 450 - 160 - 10
            max_y = 140 - 38 - 10
            new_x = random.randint(10, max(10, max_x))
            new_y = random.randint(10, max(10, max_y))
            btn_delete.place(x=new_x, y=new_y)

        def on_delete_click():
            nonlocal click_count
            click_count += 1

            if click_count == 1:
                btn_delete.configure(text="Erwischt! Noch 2x...", fg_color="#DC2626")
                jump_button()
            elif click_count == 2:
                btn_delete.configure(text="Fast! Noch 1x...", fg_color="#B91C1C")
                jump_button()
            elif click_count >= 3:
                self.reset_database()
                modal.destroy()
                messagebox.showinfo("Erfolg", "Die Datenbank wurde vollständig geleert und zurückgesetzt!")

        btn_delete = ctk.CTkButton(
            play_area, 
            text="Sicher löschen (3x)", 
            command=on_delete_click,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#EF4444", hover_color="#DC2626",
            width=160, height=38
        )
        btn_delete.place(x=145, y=50)

        btn_cancel = ctk.CTkButton(
            modal, 
            text="Abbrechen", 
            command=modal.destroy,
            font=ctk.CTkFont(size=13),
            fg_color="#475569", hover_color="#64748B",
            width=120, height=32
        )
        btn_cancel.pack(pady=(10, 0))

    def reset_database(self):
        """Löscht alle Inhalte aus der SQLite Datenbank und setzt das UI zurück."""
        self.cursor.execute("DELETE FROM protokoll")
        self.cursor.execute("DELETE FROM ausruestung")
        self.conn.commit()

        # Einsatzmodus: Alle offenen Tabs schließen & auf Ausgangszustand zurücksetzen
        for tab_name in list(self.tabview._tab_dict.keys()):
            self.tabview.delete(tab_name)

        self.tab_counter = 0
        self.update_einsatz_view_state()

        # Wache-Modus aktualisieren
        self.refresh_wache_view()

    # --- EINSATZMODUS ---
    def setup_einsatz_modus(self):
        self.einsatz_frame.grid_rowconfigure(1, weight=1)
        self.einsatz_frame.grid_columnconfigure(0, weight=1)

        # Steuerungsleiste im Einsatzmodus
        tab_bar = ctk.CTkFrame(self.einsatz_frame, height=52, fg_color="#1E293B", corner_radius=8)
        tab_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))

        btn_add = ctk.CTkButton(
            tab_bar, 
            text="➕ Neuer Kamerad / Trupp", 
            command=self.prompt_add_tab,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            fg_color="#DC2626", hover_color="#B91C1C"  # Passender roter Einsatz-Button
        )
        btn_add.pack(side="left", padx=10, pady=7)

        btn_rename = ctk.CTkButton(
            tab_bar, 
            text="✏️ Tab umbenennen", 
            command=self.prompt_rename_tab,
            font=ctk.CTkFont(size=13),
            height=38,
            fg_color="#334155", hover_color="#475569"
        )
        btn_rename.pack(side="left", padx=5, pady=7)

        btn_delete = ctk.CTkButton(
            tab_bar, 
            text="🗑️ Tab schließen", 
            command=self.delete_current_tab,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#475569", hover_color="#64748B"
        )
        btn_delete.pack(side="right", padx=10, pady=7)

        # Tabview Container (wenn Tabs aktiv sind)
        self.tabview = ctk.CTkTabview(self.einsatz_frame)

        # Leerer Ausgangszustand (wenn noch kein Kamerad angelegt ist)
        self.empty_state_frame = ctk.CTkFrame(self.einsatz_frame, fg_color="#0F172A", corner_radius=12)
        
        empty_center = ctk.CTkFrame(self.empty_state_frame, fg_color="#1E293B", corner_radius=12)
        empty_center.pack(expand=True, padx=40, pady=40)

        ctk.CTkLabel(
            empty_center,
            text="👨‍🚒 Einsatzmodus bereit (Keine Erfassung aktiv)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=40, pady=(30, 10))

        ctk.CTkLabel(
            empty_center,
            text="Klicke auf den Button, um den ersten Kameraden oder Trupp\nanzulegen und mit der PSA-Erfassung zu beginnen.",
            font=ctk.CTkFont(size=14),
            text_color="#94A3B8"
        ).pack(padx=40, pady=(0, 20))

        btn_start_add = ctk.CTkButton(
            empty_center,
            text="➕ Ersten Kameraden / Trupp anlegen",
            command=self.prompt_add_tab,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            fg_color="#DC2626", hover_color="#B91C1C"
        )
        btn_start_add.pack(padx=40, pady=(0, 30))

        self.tab_counter = 0
        self.update_einsatz_view_state()

    def update_einsatz_view_state(self):
        """Schaltet dynamisch zwischen dem leeren Bildschirm und der Tabview um."""
        if len(self.tabview._tab_dict) == 0:
            self.tabview.grid_forget()
            self.empty_state_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        else:
            self.empty_state_frame.grid_forget()
            self.tabview.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)

    def prompt_add_tab(self):
        modal = FlackerfreiesModal(self, title="Neuer Kamerad / Trupp", width=420, height=210)

        lbl = ctk.CTkLabel(
            modal, 
            text="Bitte Namen der Einsatzkraft / des Trupps eingeben:", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl.pack(pady=(20, 5))

        entry = ctk.CTkEntry(modal, font=ctk.CTkFont(size=15), width=320, placeholder_text="z. B. Kamerad / Trupp 1")
        entry.pack(pady=8)
        self.tab_counter += 1
        entry.insert(0, f"Kamerad {self.tab_counter}")
        entry.focus_set()

        def confirm():
            val = entry.get().strip()
            if not val:
                messagebox.showwarning("Hinweis", "Bitte einen Namen eingeben.", parent=modal)
                return
            if val in self.tabview._tab_dict:
                messagebox.showwarning("Hinweis", "Ein Tab mit diesem Namen existiert bereits.", parent=modal)
                return

            self.create_person_tab(val)
            self.update_einsatz_view_state()
            modal.destroy()

        entry.bind("<Return>", lambda e: confirm())

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=12)

        btn_cancel = ctk.CTkButton(
            btn_frame, text="Abbrechen", command=modal.destroy, fg_color="#475569", hover_color="#64748B", width=110, height=36
        )
        btn_cancel.pack(side="left", padx=5)

        btn_confirm = ctk.CTkButton(
            btn_frame, text="Anlegen & Starten", command=confirm, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#DC2626", hover_color="#B91C1C", width=160, height=36
        )
        btn_confirm.pack(side="left", padx=5)

    def create_person_tab(self, name):
        tab = self.tabview.add(name)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        inv_label = ctk.CTkLabel(tab, text="Barcode / Inventarnummer scannen:", font=ctk.CTkFont(size=15, weight="bold"))
        inv_label.grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=10)

        inv_entry = ctk.CTkEntry(
            tab, 
            placeholder_text="Code scannen (z. B. J-101)...", 
            font=ctk.CTkFont(size=20), 
            height=54
        )
        inv_entry.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky="ew", padx=10)
        inv_entry.focus_set()

        btn_alt = ctk.CTkButton(
            tab,
            text="🔴 ALT (Schwarz / Abgabe)",
            fg_color="#DC2626", hover_color="#991B1B",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=80,
            command=lambda: self.process_scan(name, inv_entry, "ALT (Abgabe)")
        )
        btn_alt.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="ew")

        btn_neu = ctk.CTkButton(
            tab,
            text="🟢 NEU (Weiß / Ausgabe)",
            fg_color="#16A34A", hover_color="#15803D",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=80,
            command=lambda: self.process_scan(name, inv_entry, "NEU (Ausgabe)")
        )
        btn_neu.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")

        status_banner = ctk.CTkLabel(
            tab, text="Bereit für Scan", font=ctk.CTkFont(size=15, weight="bold"), height=36, corner_radius=6, fg_color="#1E293B"
        )
        status_banner.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew", padx=10)

        log_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=14))
        log_box.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky="nsew", padx=10)
        tab.grid_rowconfigure(4, weight=1)

        tab.inv_entry = inv_entry
        tab.status_banner = status_banner
        tab.log_box = log_box

        inv_entry.bind("<Return>", lambda e: self.process_scan(name, inv_entry, "NEU (Ausgabe)"))
        self.tabview.set(name)

    def prompt_rename_tab(self):
        current_name = self.tabview.get()
        if not current_name:
            return

        modal = FlackerfreiesModal(self, title="Tab umbenennen", width=380, height=180)
        lbl = ctk.CTkLabel(modal, text=f"Neuer Name für '{current_name}':", font=ctk.CTkFont(size=14))
        lbl.pack(pady=(20, 5))

        entry = ctk.CTkEntry(modal, font=ctk.CTkFont(size=15), width=280)
        entry.pack(pady=5)
        entry.insert(0, current_name)
        entry.focus_set()

        def confirm():
            new_name = entry.get().strip()
            if not new_name or new_name == current_name:
                modal.destroy()
                return

            if new_name in self.tabview._tab_dict:
                messagebox.showwarning("Hinweis", "Ein Tab mit diesem Namen existiert bereits.", parent=modal)
                return

            old_log = self.tabview.tab(current_name).log_box.get("1.0", "end")

            self.cursor.execute("UPDATE protokoll SET person = ? WHERE person = ?", (new_name, current_name))
            self.cursor.execute("UPDATE ausruestung SET traeger = ? WHERE traeger = ?", (new_name, current_name))
            self.conn.commit()

            self.create_person_tab(new_name)
            self.tabview.tab(new_name).log_box.insert("1.0", old_log.strip() + "\n")
            self.tabview.delete(current_name)
            modal.destroy()

        entry.bind("<Return>", lambda e: confirm())
        btn = ctk.CTkButton(modal, text="Speichern", command=confirm, font=ctk.CTkFont(size=14, weight="bold"))
        btn.pack(pady=15)

    def delete_current_tab(self):
        current_name = self.tabview.get()
        if not current_name:
            return

        self.cursor.execute("SELECT COUNT(*) FROM protokoll WHERE person = ?", (current_name,))
        count = self.cursor.fetchone()[0]

        if count > 0:
            modal = FlackerfreiesModal(self, title="Schließen bestätigen", width=420, height=190)
            lbl = ctk.CTkLabel(
                modal, 
                text=f"Für '{current_name}' wurden bereits {count} Scans erfasst.\nMöchtest du den Tab wirklich schließen?",
                font=ctk.CTkFont(size=14),
                wraplength=380
            )
            lbl.pack(pady=(20, 15))

            def confirm():
                self.tabview.delete(current_name)
                self.update_einsatz_view_state()
                modal.destroy()

            btn_del = ctk.CTkButton(modal, text="Ja, Tab schließen", command=confirm, fg_color="#DC2626")
            btn_del.pack(pady=10)
        else:
            self.tabview.delete(current_name)
            self.update_einsatz_view_state()

    def process_scan(self, person, entry_widget, aktion):
        inv_nr = entry_widget.get().strip().upper()
        if not inv_nr:
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute(
            "INSERT INTO protokoll (zeitstempel, person, inv_nr, aktion) VALUES (?, ?, ?, ?)",
            (now, person, inv_nr, aktion)
        )

        neuer_status = "Schwarz" if "ALT" in aktion else "Weiß"
        neuer_traeger = "Keiner (Kontaminiert)" if "ALT" in aktion else person

        self.cursor.execute(
            "INSERT INTO ausruestung (inv_nr, bezeichnung, status, traeger) VALUES (?, 'PSA Teil', ?, ?) "
            "ON CONFLICT(inv_nr) DO UPDATE SET status=excluded.status, traeger=excluded.traeger",
            (inv_nr, neuer_status, neuer_traeger)
        )
        self.conn.commit()

        tab = self.tabview.tab(person)
        if "ALT" in aktion:
            tab.status_banner.configure(text=f"🔴 {inv_nr} abgegeben (Schwarz / Kontaminiert)", fg_color="#7F1D1D", text_color="#FECACA")
        else:
            tab.status_banner.configure(text=f"🟢 {inv_nr} ausgegeben (Weiß / Einsatzbereit)", fg_color="#14532D", text_color="#DCFCE7")

        tab.log_box.insert("1.0", f"[{now[11:]}] {inv_nr} -> {aktion}\n")
        entry_widget.delete(0, "end")
        entry_widget.focus_set()

    # --- WACHE-MODUS ---
    def setup_wache_modus(self):
        self.wache_frame.grid_rowconfigure(0, weight=1)
        self.wache_frame.grid_columnconfigure(0, weight=1)

        self.wache_tabview = ctk.CTkTabview(self.wache_frame)
        self.wache_tabview.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tab_bestand = self.wache_tabview.add("📦 Bestandsübersicht")
        self.tab_uebergabe = self.wache_tabview.add("📋 Übergabeprotokoll (Personenaufteilung)")
        self.tab_log = self.wache_tabview.add("📜 Gesamtes Einsatz-Log")

        self.setup_wache_bestand()
        self.setup_wache_uebergabe()
        self.setup_wache_log()

    def setup_wache_bestand(self):
        self.tab_bestand.grid_rowconfigure(1, weight=1)
        self.tab_bestand.grid_columnconfigure(0, weight=1)

        ctrl_card = ctk.CTkFrame(self.tab_bestand, fg_color="#1E293B", corner_radius=8)
        ctrl_card.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)

        lbl_info = ctk.CTkLabel(
            ctrl_card, 
            text="Gesamter PSA-Bestand & Hygiene-Status", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl_info.pack(side="left", padx=15, pady=12)

        btn_import = ctk.CTkButton(
            ctrl_card, 
            text="📥 FirePlan CSV Importieren", 
            command=self.import_fireplan_csv, 
            font=ctk.CTkFont(weight="bold"),
            fg_color="#2563EB", hover_color="#1D4ED8"
        )
        btn_import.pack(side="right", padx=15, pady=8)

        self.scroll_bestand = ctk.CTkScrollableFrame(self.tab_bestand, corner_radius=8, fg_color="#0F172A")
        self.scroll_bestand.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.scroll_bestand.grid_columnconfigure(0, weight=1)

    def setup_wache_uebergabe(self):
        self.tab_uebergabe.grid_rowconfigure(1, weight=1)
        self.tab_uebergabe.grid_columnconfigure(0, weight=1)
        self.tab_uebergabe.grid_columnconfigure(1, weight=1)

        ctrl_card = ctk.CTkFrame(self.tab_uebergabe, fg_color="#1E293B", corner_radius=8)
        ctrl_card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=5)

        lbl = ctk.CTkLabel(ctrl_card, text="Kamerad / Trupp auswählen:", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(side="left", padx=15, pady=12)

        self.combo_persons = ctk.CTkComboBox(
            ctrl_card, 
            values=["Keine Daten"], 
            command=self.load_person_uebergabe, 
            width=240,
            font=ctk.CTkFont(size=14)
        )
        self.combo_persons.pack(side="left", padx=10, pady=8)

        btn_pdf = ctk.CTkButton(
            ctrl_card, 
            text="📄 PDF Übergabeschein drucken", 
            command=lambda: self.export_pdf(self.combo_persons.get()),
            fg_color="#16A34A", hover_color="#15803D",
            font=ctk.CTkFont(weight="bold")
        )
        btn_pdf.pack(side="right", padx=15, pady=8)

        # Spalte ALT
        col_alt_frame = ctk.CTkFrame(self.tab_uebergabe, fg_color="#1E293B", corner_radius=8)
        col_alt_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 5), pady=5)
        col_alt_frame.grid_rowconfigure(1, weight=1)
        col_alt_frame.grid_columnconfigure(0, weight=1)

        self.lbl_alt_title = ctk.CTkLabel(
            col_alt_frame, 
            text="🔴 Abgegebene PSA (ALT / Schwarz)", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FECACA", fg_color="#7F1D1D", corner_radius=6, height=35
        )
        self.lbl_alt_title.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        self.scroll_alt = ctk.CTkScrollableFrame(col_alt_frame, fg_color="#0F172A", corner_radius=6)
        self.scroll_alt.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.scroll_alt.grid_columnconfigure(0, weight=1)

        # Spalte NEU
        col_neu_frame = ctk.CTkFrame(self.tab_uebergabe, fg_color="#1E293B", corner_radius=8)
        col_neu_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 5), pady=5)
        col_neu_frame.grid_rowconfigure(1, weight=1)
        col_neu_frame.grid_columnconfigure(0, weight=1)

        self.lbl_neu_title = ctk.CTkLabel(
            col_neu_frame, 
            text="🟢 Ausgegebene PSA (NEU / Weiß)", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#DCFCE7", fg_color="#14532D", corner_radius=6, height=35
        )
        self.lbl_neu_title.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        self.scroll_neu = ctk.CTkScrollableFrame(col_neu_frame, fg_color="#0F172A", corner_radius=6)
        self.scroll_neu.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.scroll_neu.grid_columnconfigure(0, weight=1)

    def setup_wache_log(self):
        self.tab_log.grid_rowconfigure(1, weight=1)
        self.tab_log.grid_columnconfigure(0, weight=1)

        ctrl_card = ctk.CTkFrame(self.tab_log, fg_color="#1E293B", corner_radius=8)
        ctrl_card.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)

        lbl_info = ctk.CTkLabel(
            ctrl_card, 
            text="Lückenloses Einsatz-Protokoll (Revisionssicher)", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl_info.pack(side="left", padx=15, pady=12)

        btn_pdf = ctk.CTkButton(
            ctrl_card, 
            text="📄 Gesamt-Log als PDF exportieren", 
            command=lambda: self.export_pdf(None),
            fg_color="#2563EB", hover_color="#1D4ED8",
            font=ctk.CTkFont(weight="bold")
        )
        btn_pdf.pack(side="right", padx=15, pady=8)

        self.scroll_log = ctk.CTkScrollableFrame(self.tab_log, corner_radius=8, fg_color="#0F172A")
        self.scroll_log.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.scroll_log.grid_columnconfigure(0, weight=1)

    def refresh_wache_view(self):
        for w in self.scroll_bestand.winfo_children():
            w.destroy()

        self.cursor.execute("SELECT inv_nr, bezeichnung, status, traeger FROM ausruestung ORDER BY inv_nr")
        rows = self.cursor.fetchall()

        if not rows:
            ctk.CTkLabel(self.scroll_bestand, text="Keine Bestandsdaten vorhanden (Datenbank ist leer).", font=ctk.CTkFont(size=14)).pack(pady=20)

        for r in rows:
            card = ctk.CTkFrame(self.scroll_bestand, fg_color="#1E293B", corner_radius=6)
            card.pack(fill="x", padx=5, pady=4)
            card.grid_columnconfigure(1, weight=1)

            inv_lbl = ctk.CTkLabel(card, text=r[0], font=ctk.CTkFont(size=14, weight="bold"), width=100, fg_color="#334155", corner_radius=4)
            inv_lbl.grid(row=0, column=0, padx=10, pady=8)

            bez_lbl = ctk.CTkLabel(card, text=r[1], font=ctk.CTkFont(size=14), anchor="w")
            bez_lbl.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

            is_schwarz = r[2] == "Schwarz"
            status_chip = ctk.CTkLabel(
                card, 
                text="🔴 Schwarz" if is_schwarz else "🟢 Weiß",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#7F1D1D" if is_schwarz else "#14532D",
                text_color="#FECACA" if is_schwarz else "#DCFCE7",
                corner_radius=4, width=110
            )
            status_chip.grid(row=0, column=2, padx=10, pady=8)

            traeger_lbl = ctk.CTkLabel(card, text=f"📍 {r[3]}", font=ctk.CTkFont(size=13), text_color="#94A3B8", width=180, anchor="e")
            traeger_lbl.grid(row=0, column=3, padx=10, pady=8)

        self.cursor.execute("SELECT DISTINCT person FROM protokoll")
        persons = [r[0] for r in self.cursor.fetchall()]
        if persons:
            self.combo_persons.configure(values=persons)
            current_selected = self.combo_persons.get()
            if current_selected not in persons:
                self.combo_persons.set(persons[0])
                current_selected = persons[0]
            self.load_person_uebergabe(current_selected)
        else:
            self.combo_persons.configure(values=["Keine Daten"])
            self.combo_persons.set("Keine Daten")
            self.load_person_uebergabe("")

        for w in self.scroll_log.winfo_children():
            w.destroy()

        self.cursor.execute("SELECT zeitstempel, person, inv_nr, aktion FROM protokoll ORDER BY id DESC")
        logs = self.cursor.fetchall()

        if not logs:
            ctk.CTkLabel(self.scroll_log, text="Keine Log-Einträge vorhanden (Datenbank ist leer).", font=ctk.CTkFont(size=14)).pack(pady=20)

        for l in logs:
            card = ctk.CTkFrame(self.scroll_log, fg_color="#1E293B", corner_radius=6)
            card.pack(fill="x", padx=5, pady=3)
            card.grid_columnconfigure(1, weight=1)

            time_lbl = ctk.CTkLabel(card, text=l[0], font=ctk.CTkFont(size=13), text_color="#94A3B8", width=160)
            time_lbl.grid(row=0, column=0, padx=10, pady=6)

            pers_lbl = ctk.CTkLabel(card, text=f"👤 {l[1]}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            pers_lbl.grid(row=0, column=1, padx=10, pady=6, sticky="ew")

            inv_lbl = ctk.CTkLabel(card, text=l[2], font=ctk.CTkFont(size=13, weight="bold"), width=90, fg_color="#334155", corner_radius=4)
            inv_lbl.grid(row=0, column=2, padx=10, pady=6)

            is_alt = "ALT" in l[3]
            akt_chip = ctk.CTkLabel(
                card,
                text="🔴 Abgabe" if is_alt else "🟢 Ausgabe",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#7F1D1D" if is_alt else "#14532D",
                text_color="#FECACA" if is_alt else "#DCFCE7",
                corner_radius=4, width=100
            )
            akt_chip.grid(row=0, column=3, padx=10, pady=6)

    def load_person_uebergabe(self, person):
        for w in self.scroll_alt.winfo_children():
            w.destroy()
        for w in self.scroll_neu.winfo_children():
            w.destroy()

        if not person or person == "Keine Daten":
            self.lbl_alt_title.configure(text="🔴 Abgegebene PSA (0 Teile)")
            self.lbl_neu_title.configure(text="🟢 Ausgegebene PSA (0 Teile)")
            ctk.CTkLabel(self.scroll_alt, text="Keine Rückgaben vorhanden.", font=ctk.CTkFont(size=13), text_color="#64748B").pack(pady=15)
            ctk.CTkLabel(self.scroll_neu, text="Keine Ausgaben vorhanden.", font=ctk.CTkFont(size=13), text_color="#64748B").pack(pady=15)
            return

        self.cursor.execute(
            "SELECT p.zeitstempel, p.inv_nr, p.aktion, COALESCE(a.bezeichnung, 'PSA Teil') "
            "FROM protokoll p LEFT JOIN ausruestung a ON p.inv_nr = a.inv_nr "
            "WHERE p.person = ? ORDER BY p.id DESC", 
            (person,)
        )
        rows = self.cursor.fetchall()

        alt_items = [r for r in rows if "ALT" in r[2]]
        neu_items = [r for r in rows if "NEU" in r[2]]

        self.lbl_alt_title.configure(text=f"🔴 Abgegebene PSA ({len(alt_items)} Teile - Schwarz)")
        self.lbl_neu_title.configure(text=f"🟢 Ausgegebene PSA ({len(neu_items)} Teile - Weiß)")

        if not alt_items:
            ctk.CTkLabel(self.scroll_alt, text="Keine Rückgaben vorhanden.", font=ctk.CTkFont(size=13), text_color="#64748B").pack(pady=15)
        else:
            for r in alt_items:
                card = ctk.CTkFrame(self.scroll_alt, fg_color="#1E293B", corner_radius=6)
                card.pack(fill="x", padx=4, pady=4)
                
                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=8, pady=(6, 2))
                
                ctk.CTkLabel(top_row, text=r[1], font=ctk.CTkFont(size=14, weight="bold"), fg_color="#334155", corner_radius=4, width=80).pack(side="left")
                ctk.CTkLabel(top_row, text=r[3], font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=8)
                
                time_lbl = ctk.CTkLabel(card, text=f"🕒 {r[0]}", font=ctk.CTkFont(size=12), text_color="#94A3B8")
                time_lbl.pack(anchor="w", padx=8, pady=(0, 6))

        if not neu_items:
            ctk.CTkLabel(self.scroll_neu, text="Keine Ausgaben vorhanden.", font=ctk.CTkFont(size=13), text_color="#64748B").pack(pady=15)
        else:
            for r in neu_items:
                card = ctk.CTkFrame(self.scroll_neu, fg_color="#1E293B", corner_radius=6)
                card.pack(fill="x", padx=4, pady=4)
                
                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=8, pady=(6, 2))
                
                ctk.CTkLabel(top_row, text=r[1], font=ctk.CTkFont(size=14, weight="bold"), fg_color="#334155", corner_radius=4, width=80).pack(side="left")
                ctk.CTkLabel(top_row, text=r[3], font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=8)
                
                time_lbl = ctk.CTkLabel(card, text=f"🕒 {r[0]}", font=ctk.CTkFont(size=12), text_color="#94A3B8")
                time_lbl.pack(anchor="w", padx=8, pady=(0, 6))

    def import_fireplan_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv"), ("Textdateien", "*.txt")])
        if not file_path:
            return

        try:
            imported = 0
            with open(file_path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    parts = [p.strip(' "') for p in line.replace(";", ",").split(",")]
                    if len(parts) >= 2 and parts[0] != "Inventarnummer":
                        inv_nr, bez = parts[0], parts[1]
                        self.cursor.execute(
                            "INSERT INTO ausruestung (inv_nr, bezeichnung, status, traeger) VALUES (?, ?, 'Weiß', 'Frei') "
                            "ON CONFLICT(inv_nr) DO UPDATE SET bezeichnung=excluded.bezeichnung",
                            (inv_nr, bez)
                        )
                        imported += 1
            self.conn.commit()
            messagebox.showinfo("Import erfolgreich", f"Es wurden {imported} Ausrüstungsgegenstände importiert.")
            self.refresh_wache_view()
        except Exception as e:
            messagebox.showerror("Importfehler", f"Fehler beim Einlesen der CSV:\n{e}")

    def export_pdf(self, person=None):
        if not HAS_REPORTLAB:
            messagebox.showerror(
                "Paket fehlt", 
                "Das Paket 'reportlab' ist nicht installiert.\n\nBitte im VS Code Terminal ausführen:\npip install reportlab"
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Dokument", "*.pdf")],
            initialfile=f"PSA_Protokoll_{person if person and person != 'Keine Daten' else 'Gesamt'}.pdf"
        )
        if not file_path:
            return

        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#0F172A'))
        title_text = f"PSA-Track Übergabeprotokoll: {person}" if person and person != "Keine Daten" else "PSA-Track Gesamteinsatz-Protokoll"
        
        story.append(Paragraph(title_text, title_style))
        story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S Uhr')}", styles['Normal']))
        story.append(Spacer(1, 15))

        if person and person != "Keine Daten":
            self.cursor.execute("SELECT zeitstempel, inv_nr, aktion FROM protokoll WHERE person = ? ORDER BY id DESC", (person,))
            rows = self.cursor.fetchall()
            data = [["Zeitstempel", "Inventarnummer", "Aktion / Status"]]
            for r in rows:
                data.append([r[0], r[1], r[2]])
        else:
            self.cursor.execute("SELECT zeitstempel, person, inv_nr, aktion FROM protokoll ORDER BY id DESC")
            rows = self.cursor.fetchall()
            data = [["Zeitstempel", "Person / Trupp", "Inventarnummer", "Aktion"]]
            for r in rows:
                data.append([r[0], r[1], r[2], r[3]])

        if len(data) == 1:
            data.append(["Keine Einträge vorhanden", "-", "-", "-"] if not person else ["Keine Einträge", "-", "-"])

        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(t)
        story.append(Spacer(1, 40))

        sig_data = [
            ["__________________________________________", "__________________________________________"],
            ["Unterschrift Gerätewart / Ausgeber", "Unterschrift Träger / Empfänger"]
        ]
        sig_table = Table(sig_data, colWidths=[250, 250], hAlign='LEFT')
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#475569')),
        ]))
        story.append(sig_table)

        doc.build(story)
        messagebox.showinfo("PDF Export", f"Das Protokoll wurde erfolgreich als PDF gespeichert:\n{file_path}")


if __name__ == "__main__":
    app = PSATrackApp()
    app.mainloop()
