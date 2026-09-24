import sqlite3
from datetime import datetime
import customtkinter as ctk

# CustomTkinter Design-Einstellungen (Dark Mode & Blaues Theme)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ConfirmationModal(ctk.CTkToplevel):
    """Touch-optimierter Dialog zur Bestätigung von Löschvorgängen"""
    def __init__(self, parent, title, message, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.geometry("480x240")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Zentrierung auf dem Bildschirm
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (480 // 2)
        y = (self.winfo_screenheight() // 2) - (240 // 2)
        self.geometry(f"480x240+{x}+{y}")

        lbl_icon = ctk.CTkLabel(self, text="⚠️", font=ctk.CTkFont(size=36))
        lbl_icon.pack(pady=(15, 5))

        lbl_msg = ctk.CTkLabel(
            self,
            text=message,
            wraplength=440,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl_msg.pack(pady=5, padx=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Abbrechen",
            width=180,
            height=50,
            fg_color="#424242",
            hover_color="#616161",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=10, expand=True)

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Ja, Löschen",
            width=180,
            height=50,
            fg_color="#D32F2F",
            hover_color="#9A0007",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: [self.destroy(), on_confirm()]
        )
        confirm_btn.pack(side="right", padx=10, expand=True)


class RenameModal(ctk.CTkToplevel):
    """Dialog zum Umbenennen von Kameraden/Trupps"""
    def __init__(self, parent, old_name, on_rename):
        super().__init__(parent)
        self.on_rename = on_rename
        self.title("Kamerad / Trupp umbenennen")
        self.geometry("450x230")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (230 // 2)
        self.geometry(f"450x230+{x}+{y}")

        lbl = ctk.CTkLabel(
            self,
            text=f"Neuer Name für '{old_name}':",
            font=ctk.CTkFont(size=17, weight="bold")
        )
        lbl.pack(pady=(20, 10))

        self.entry = ctk.CTkEntry(
            self,
            font=ctk.CTkFont(size=18),
            height=45,
            width=350
        )
        self.entry.insert(0, old_name)
        self.entry.pack(pady=10)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self.submit())

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Abbrechen",
            height=45,
            width=150,
            fg_color="#424242",
            hover_color="#616161",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=10, expand=True)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Speichern",
            height=45,
            width=150,
            fg_color="#1E88E5",
            hover_color="#1565C0",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.submit
        )
        save_btn.pack(side="right", padx=10, expand=True)

    def submit(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.on_rename(new_name)
            self.destroy()


class PSATrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("PSA-Track - Digitales Einsatz- & Hygiene-Management")

        # Für Tablet-Auflösung optimiert (z.B. 1280x720 / 1300x700)
        self.geometry("1280x720")
        self.minsize(1024, 600)

        # Datenbank initialisieren
        self.init_db()

        # Interne Tracking-Variablen
        self.person_tabs = {}  # name -> {'entry': entry_widget, 'log': log_box, 'banner': banner_label}
        self.person_counter = 0

        # Layout Haupt-Container
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top Bar (Großer Touch-Umschalter für Modi)
        self.top_bar = ctk.CTkFrame(self, height=65, corner_radius=10)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 5))
        self.top_bar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="🚒 PSA-TRACK",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=20)

        # Extra großer Touch-SegmentedButton
        self.mode_segmented = ctk.CTkSegmentedButton(
            self.top_bar,
            values=["Einsatzmodus", "Wache-Modus"],
            command=self.switch_mode,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=48,
            selected_color="#1E88E5",
            selected_hover_color="#1565C0"
        )
        self.mode_segmented.pack(side="right", padx=15, pady=8)
        self.mode_segmented.set("Einsatzmodus")

        # Haupt-Bereiche (Frames)
        self.einsatz_frame = ctk.CTkFrame(self)
        self.wache_frame = ctk.CTkFrame(self)

        self.setup_einsatz_modus()
        self.setup_wache_modus()

        # Standardmäßig Einsatzmodus anzeigen
        self.einsatz_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=5)

    def init_db(self):
        self.conn = sqlite3.connect("psa_track.db")
        self.cursor = self.conn.cursor()

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
        # Sanfter Übergangs-Effekt
        if mode == "Einsatzmodus":
            self.wache_frame.grid_forget()
            self.einsatz_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=5)
            self.animate_frame_appear(self.einsatz_frame)
        else:
            self.einsatz_frame.grid_forget()
            self.refresh_wache_tables()
            self.wache_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=5)
            self.animate_frame_appear(self.wache_frame)

    def animate_frame_appear(self, frame):
        """Kurzer visueller Flash beim Moduswechsel"""
        original_color = frame.cget("fg_color")
        frame.configure(fg_color="#2B2D30")
        self.after(60, lambda: frame.configure(fg_color=original_color))

    # --- EINSATZMODUS ---
    def setup_einsatz_modus(self):
        self.einsatz_frame.grid_rowconfigure(0, weight=1)
        self.einsatz_frame.grid_columnconfigure(0, weight=1)

        # Großer Touch-Tabview
        self.tabview = ctk.CTkTabview(
            self.einsatz_frame,
            segmented_button_fg_color="#1A1C1E",
            segmented_button_selected_color="#1E88E5",
            segmented_button_selected_hover_color="#1565C0"
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        # Schriftgröße & Höhe der Tab-Schaltflächen vergrößern
        self.tabview._segmented_button.configure(
            font=ctk.CTkFont(size=17, weight="bold"),
            height=48
        )

        # Aktions-Leiste unter den Tabs
        action_bar = ctk.CTkFrame(self.einsatz_frame, height=55, fg_color="transparent")
        action_bar.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        self.add_tab_btn = ctk.CTkButton(
            action_bar,
            text="➕ Neuer Kamerad / Trupp",
            command=self.prompt_add_person,
            font=ctk.CTkFont(size=17, weight="bold"),
            height=50,
            fg_color="#2E7D32",
            hover_color="#1B5E20"
        )
        self.add_tab_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Ersten Standard-Tab anlegen
        self.create_person_tab("Kamerad 1")

    def prompt_add_person(self):
        dialog = ctk.CTkInputDialog(
            text="Name des Kameraden oder Trupps eingeben:",
            title="Neuen Kamerad anlegen"
        )
        name = dialog.get_input()
        if name and name.strip():
            clean_name = name.strip()
            if clean_name in self.person_tabs:
                clean_name = f"{clean_name} (neu)"
            self.create_person_tab(clean_name)

    def create_person_tab(self, name, log_history=""):
        tab = self.tabview.add(name)

        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        # Top-Bar innerhalb des Tabs (Header, Umbenennen & Löschen)
        tab_header = ctk.CTkFrame(tab, fg_color="transparent")
        tab_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 8))

        lbl_name = ctk.CTkLabel(
            tab_header,
            text=f"👤 {name}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        lbl_name.pack(side="left", padx=10)

        btn_del = ctk.CTkButton(
            tab_header,
            text="🗑️ Tab löschen",
            width=130,
            height=38,
            fg_color="#C62828",
            hover_color="#8E0000",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda n=name: self.confirm_and_delete_tab(n)
        )
        btn_del.pack(side="right", padx=5)

        btn_rename = ctk.CTkButton(
            tab_header,
            text="✏️ Umbenennen",
            width=130,
            height=38,
            fg_color="#424242",
            hover_color="#616161",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda n=name: self.open_rename_modal(n)
        )
        btn_rename.pack(side="right", padx=5)

        # Animierter Status-Banner (Toast-Feedback)
        banner = ctk.CTkLabel(
            tab,
            text="Bereit für Scan...",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2B2B2B",
            corner_radius=8,
            height=40
        )
        banner.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        # Eingabefeld Inventarnummer (Groß & Touch-freundlich)
        inv_entry = ctk.CTkEntry(
            tab,
            placeholder_text="Inventarnummer scannen (z.B. J-101)...",
            font=ctk.CTkFont(size=22),
            height=58
        )
        inv_entry.grid(row=2, column=0, columnspan=2, pady=(0, 12), sticky="ew", padx=5)
        inv_entry.focus()
        inv_entry.bind("<Return>", lambda e, n=name, ent=inv_entry: self.process_scan(n, ent, "NEU (Ausgabe)"))

        # Große Touch-Buttons
        btn_alt = ctk.CTkButton(
            tab,
            text="🔴 ALT\n(Abgabe / Schwarz)",
            fg_color="#D32F2F",
            hover_color="#9A0007",
            font=ctk.CTkFont(size=20, weight="bold"),
            height=90,
            command=lambda n=name, ent=inv_entry: self.process_scan(n, ent, "ALT (Abgabe)")
        )
        btn_alt.grid(row=3, column=0, padx=8, pady=5, sticky="ew")

        btn_neu = ctk.CTkButton(
            tab,
            text="🟢 NEU\n(Ausgabe / Weiß)",
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(size=20, weight="bold"),
            height=90,
            command=lambda n=name, ent=inv_entry: self.process_scan(n, ent, "NEU (Ausgabe)")
        )
        btn_neu.grid(row=3, column=1, padx=8, pady=5, sticky="ew")

        # Protokoll-Box für diesen Tab
        log_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=15))
        log_box.grid(row=4, column=0, columnspan=2, pady=(10, 5), sticky="nsew", padx=5)

        if log_history:
            log_box.insert("1.0", log_history)

        # Speichern im Tab-Tracking
        self.person_tabs[name] = {
            'entry': inv_entry,
            'log': log_box,
            'banner': banner
        }

        # Direkt auf den neu angelegten Tab wechseln
        self.tabview.set(name)

    def open_rename_modal(self, old_name):
        RenameModal(self, old_name, lambda new_name: self.rename_person_tab(old_name, new_name))

    def rename_person_tab(self, old_name, new_name):
        if old_name == new_name or not new_name:
            return

        if new_name in self.person_tabs:
            new_name = f"{new_name}_{datetime.now().strftime('%H%M%S')}"

        # 1. Log-Inhalt sichern
        log_content = self.person_tabs[old_name]['log'].get("1.0", "end-1c")

        # 2. Datenbank-Einträge aktualisieren
        self.cursor.execute("UPDATE protokoll SET person = ? WHERE person = ?", (new_name, old_name))
        self.cursor.execute("UPDATE ausruestung SET traeger = ? WHERE traeger = ?", (new_name, old_name))
        self.conn.commit()

        # 3. Alten Tab löschen & neuen Tab mit altem Inhalt erstellen
        del self.person_tabs[old_name]
        self.tabview.delete(old_name)

        self.create_person_tab(new_name, log_history=log_content)

    def confirm_and_delete_tab(self, person_name):
        # Prüfen, ob für diesen Kameraden bereits Einträge in der DB existieren
        self.cursor.execute("SELECT COUNT(*) FROM protokoll WHERE person = ?", (person_name,))
        count = self.cursor.fetchone()[0]

        if count == 0:
            # Wenn leer -> Sofort löschen
            self.delete_person_tab(person_name)
        else:
            # Wenn Einträge vorhanden -> Dialog mit Warnung & Bestätigung
            msg = f"Für '{person_name}' wurden bereits {count} Buchung(en) erfasst!\n\nSoll der Tab wirklich gelöscht werden?"
            ConfirmationModal(
                self,
                "Kamerad löschen",
                msg,
                on_confirm=lambda: self.delete_person_tab(person_name)
            )

    def delete_person_tab(self, person_name):
        if person_name in self.person_tabs:
            del self.person_tabs[person_name]
            self.tabview.delete(person_name)

        # Falls alle Tabs gelöscht wurden, automatisch einen frischen Standard-Tab anlegen
        if len(self.person_tabs) == 0:
            self.person_counter += 1
            self.create_person_tab(f"Kamerad {self.person_counter}")

    def process_scan(self, person, entry_widget, aktion):
        inv_nr = entry_widget.get().strip().upper()
        if not inv_nr:
            self.trigger_banner_animation(person, "⚠️ Bitte Inventarnummer eingeben!", color="#F57C00")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # In Datenbank protokollieren
        self.cursor.execute(
            "INSERT INTO protokoll (zeitstempel, person, inv_nr, aktion) VALUES (?, ?, ?, ?)",
            (now, person, inv_nr, aktion)
        )

        neuer_status = "Schwarz" if "ALT" in aktion else "Weiß"
        neuer_traeger = "Keiner (Kontaminiert)" if "ALT" in aktion else person

        self.cursor.execute(
            "UPDATE ausruestung SET status = ?, traeger = ? WHERE inv_nr = ?",
            (neuer_status, neuer_traeger, inv_nr)
        )

        self.conn.commit()

        # Log-Box im Tab aktualisieren
        log_msg = f"[{now[11:]}] {aktion}: {inv_nr}\n"
        self.person_tabs[person]['log'].insert("1.0", log_msg)

        # Eingabefeld leeren & Fokus für schnelles Weiterscannen halten
        entry_widget.delete(0, "end")
        entry_widget.focus()

        # Schnell-Animation ausführen
        is_neu = "NEU" in aktion
        bg_color = "#2E7D32" if is_neu else "#D32F2F"
        status_text = f"✅ {inv_nr} als NEU gebucht!" if is_neu else f"🔴 {inv_nr} als ALT gebucht!"
        self.trigger_banner_animation(person, status_text, bg_color)

    def trigger_banner_animation(self, person, text, color):
        """Schnelle Flash-Animation für den Status-Banner"""
        if person not in self.person_tabs:
            return

        banner = self.person_tabs[person]['banner']
        banner.configure(text=text, fg_color=color)

        # Licht-Pulsieren für spürbares Touch-Feedback
        self.after(150, lambda: banner.configure(fg_color=self.lighten_color(color)))
        self.after(350, lambda: banner.configure(fg_color=color))
        self.after(2000, lambda: banner.configure(text="Bereit für nächsten Scan...", fg_color="#2B2B2B"))

    def lighten_color(self, hex_color):
        """Hilfsfunktion zum Aufhellen von Hex-Farben für Pulsoffekte"""
        if hex_color == "#2E7D32":
            return "#4CAF50"
        elif hex_color == "#D32F2F":
            return "#EF5350"
        return "#FFB74D"

    # --- WACHE-MODUS ---
    def setup_wache_modus(self):
        self.wache_frame.grid_rowconfigure(1, weight=1)
        self.wache_frame.grid_columnconfigure(0, weight=1)
        self.wache_frame.grid_columnconfigure(1, weight=1)

        # Links: Ausrüstungs-Bestand
        lbl_left = ctk.CTkLabel(
            self.wache_frame,
            text="📦 Ausrüstungs-Bestand",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_left.grid(row=0, column=0, pady=10)

        self.tb_ausruestung = ctk.CTkTextbox(
            self.wache_frame,
            font=ctk.CTkFont(family="Consolas", size=14)
        )
        self.tb_ausruestung.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # Rechts: Einsatz-Protokoll
        lbl_right = ctk.CTkLabel(
            self.wache_frame,
            text="📜 Einsatz-Protokoll (Historie)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_right.grid(row=0, column=1, pady=10)

        self.tb_protokoll = ctk.CTkTextbox(
            self.wache_frame,
            font=ctk.CTkFont(family="Consolas", size=14)
        )
        self.tb_protokoll.grid(row=1, column=1, padx=12, pady=(0, 12), sticky="nsew")

    def refresh_wache_tables(self):
        self.tb_ausruestung.delete("1.0", "end")
        self.cursor.execute("SELECT inv_nr, bezeichnung, status, traeger FROM ausruestung")
        rows = self.cursor.fetchall()
        header = f"{'INV-NR':<10} | {'BEZEICHNUNG':<22} | {'STATUS':<8} | {'TRÄGER'}\n"
        self.tb_ausruestung.insert("end", header + "─" * 65 + "\n")
        for r in rows:
            self.tb_ausruestung.insert("end", f"{r[0]:<10} | {r[1]:<22} | {r[2]:<8} | {r[3]}\n")

        self.tb_protokoll.delete("1.0", "end")
        self.cursor.execute("SELECT zeitstempel, person, inv_nr, aktion FROM protokoll ORDER BY id DESC")
        p_rows = self.cursor.fetchall()
        p_header = f"{'ZEITSTEMPEL':<19} | {'PERSON / TRUPP':<18} | {'INV-NR':<8} | {'AKTION'}\n"
        self.tb_protokoll.insert("end", p_header + "─" * 68 + "\n")
        for pr in p_rows:
            self.tb_protokoll.insert("end", f"{pr[0]:<19} | {pr[1]:<18} | {pr[2]:<8} | {pr[3]}\n")


if __name__ == "__main__":
    app = PSATrackApp()
    app.mainloop()