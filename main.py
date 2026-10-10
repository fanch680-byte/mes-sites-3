# -*- coding: utf-8 -*-
import customtkinter as ctk
import webbrowser
import os
import json
from PIL import Image
from io import BytesIO
import ctypes
from tkinter import filedialog, HORIZONTAL
import re
import unicodedata
import urllib.request

# === DPI AWARENESS ===
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# === CACHE ICÔNES ===
_icon_cache = {}
_favicon_cache = {}

def charger_icone_local(path, size=(24, 24)):
    if not path or not os.path.isfile(path):
        return None
    if path in _icon_cache:
        return _icon_cache[path]
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(size, Image.LANCZOS)
        ctk_img = ctk.CTkImage(img, size=size)
        _icon_cache[path] = ctk_img
        return ctk_img
    except:
        return None

def get_favicon_sync(domaine, size=(24, 24)):
    if not domaine or domaine == "default":
        return None
    if domaine in _favicon_cache:
        return _favicon_cache[domaine]
    
    urls = [
        f"https://{domaine}/favicon.ico",
        f"https://www.{domaine}/favicon.ico",
        f"https://www.google.com/s2/favicons?domain={domaine}&sz=32"
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = response.read()
                if data:
                    img = Image.open(BytesIO(data)).convert("RGBA")
                    img.thumbnail(size, Image.LANCZOS)
                    ctk_img = ctk.CTkImage(img, size=size)
                    _favicon_cache[domaine] = ctk_img
                    _icon_cache[domaine] = ctk_img
                    return ctk_img
        except:
            continue
    return None

# === NOUVELLE FONCTION : SAUVEGARDER TOUS LES FAVICONS ===
def sauvegarder_tous_les_favicons():
    import os
    import urllib.request
    from urllib.parse import urlparse

    dossier = "favicons"
    os.makedirs(dossier, exist_ok=True)
    
    total = 0
    sauvegardes = 0

    for cat, sites in categories.items():
        for site in sites:
            if len(site) < 2:
                continue
            url = site[1].strip()
            try:
                parsed = urlparse(url)
                domaine = parsed.netloc.lower()
                if not domaine:
                    continue
                if domaine.startswith("www."):
                    domaine = domaine[4:]
                if not domaine:
                    continue

                chemin = os.path.join(dossier, f"{domaine}.png")
                if os.path.isfile(chemin):
                    continue

                # Essayer plusieurs sources
                sources = [
                    f"https://{domaine}/favicon.ico",
                    f"https://www.{domaine}/favicon.ico",
                    f"https://www.google.com/s2/favicons?domain={domaine}&sz=64"
                ]
                for src in sources:
                    try:
                        req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                data = resp.read()
                                if data:
                                    img = Image.open(BytesIO(data)).convert("RGBA")
                                    img.save(chemin, "PNG")
                                    sauvegardes += 1
                                    break
                    except:
                        continue
                total += 1
            except Exception as e:
                continue

    msg = f"✅ {sauvegardes}/{total} favicons sauvegardés"
    status_label.configure(text=msg, text_color="#4CAF50")
    app.after(4000, lambda: status_label.configure(text=""))

# === CHARGEMENT DU JSON ===
FICHIER_JSON = "sites.json"

def nettoyer_texte(s):
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r'[\s\u00A0\u200B\u202F]+', ' ', s)
    return s.strip()

if os.path.exists(FICHIER_JSON):
    with open(FICHIER_JSON, "r", encoding="utf-8-sig") as f:
        raw_data = json.load(f)
    categories = {
        nettoyer_texte(cat): [
            [nettoyer_texte(site[0]), site[1], site[2] if len(site) > 2 else ""]
            for site in sites
        ]
        for cat, sites in raw_data.items()
        if nettoyer_texte(cat)
    }
else:
    categories = {
        "Test": [["Exemple", "https://example.com", ""]]
    }
    with open(FICHIER_JSON, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

def sauvegarder():
    with open(FICHIER_JSON, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

# === APPLICATION ===
app = ctk.CTk()
app.title("Mes Sites Web")
app.geometry("1200x700+90+10")
app.minsize(900, 500)

categorie_active = next(iter(categories.keys())) if categories else "Test"

# === GLOBAL POUR CATÉGORIES ===
global cat_container, status_label
cat_container = None

# === FONCTIONS ===
def ouvrir_site(url):
    if not url:
        return
    url = url.strip()
    if url.lower() in ["outlook", "mail"]:
        try:
            os.startfile(url)
        except:
            webbrowser.open("https://outlook.live.com/")
    elif url.startswith(("http://", "https://")):
        webbrowser.open(url)
    else:
        webbrowser.open("https://" + url)

def supprimer_site(cat, idx):
    if cat in categories and 0 <= idx < len(categories[cat]):
        del categories[cat][idx]
        if not categories[cat]:
            del categories[cat]
        sauvegarder()
        charger_categorie(cat)

def supprimer_categorie(cat):
    if cat in categories:
        del categories[cat]
        sauvegarder()
        if categories:
            premiere = next(iter(categories.keys()))
            charger_categorie(premiere)
        else:
            categories["Test"] = []
            sauvegarder()
            charger_categorie("Test")

def ajouter_site():
    top = ctk.CTkToplevel(app)
    top.title("➕ Ajouter un site")
    top.transient(app)
    top.grab_set()
    top.geometry("480x450+{}+{}".format(app.winfo_rootx()+100, app.winfo_rooty()+50))

    cat_var = ctk.StringVar(value=categorie_active)
    titre_var = ctk.StringVar()
    url_var = ctk.StringVar()
    icone_var = ctk.StringVar()

    ctk.CTkLabel(top, text="📌 Catégorie", font=("Segoe UI", 13)).pack(anchor="w", padx=20, pady=(10,0))
    ctk.CTkEntry(top, textvariable=cat_var, height=30).pack(fill="x", padx=20, pady=(0,8))

    ctk.CTkLabel(top, text="🔤 Nom", font=("Segoe UI", 13)).pack(anchor="w", padx=20, pady=(5,0))
    ctk.CTkEntry(top, textvariable=titre_var, height=30).pack(fill="x", padx=20, pady=(0,8))

    ctk.CTkLabel(top, text="🔗 URL (https://...)", font=("Segoe UI", 13)).pack(anchor="w", padx=20, pady=(5,0))
    ctk.CTkEntry(top, textvariable=url_var, height=30).pack(fill="x", padx=20, pady=(0,8))

    ctk.CTkLabel(top, text="🖼️ Icône (facultatif)", font=("Segoe UI", 13)).pack(anchor="w", padx=20, pady=(5,0))
    icone_entry = ctk.CTkEntry(top, textvariable=icone_var, height=30)
    icone_entry.pack(fill="x", padx=20, pady=(0,8))

    def parcourir():
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.ico *.webp")])
        if path: icone_var.set(path)
    ctk.CTkButton(top, text="📷 Parcourir...", command=parcourir, width=120).pack(pady=5)

    def enregistrer():
        cat = cat_var.get().strip().title()
        titre = titre_var.get().strip()
        url = url_var.get().strip()
        icone = icone_var.get().strip()
        if not cat or not titre or not url:
            err = ctk.CTkLabel(top, text="❌ Tous les champs requis", text_color="red")
            err.pack()
            top.after(3000, err.destroy)
            return
        categories.setdefault(cat, []).append([titre, url, icone])
        sauvegarder()
        charger_categorie(cat)
        top.destroy()

    ctk.CTkButton(top, text="✅ Ajouter", command=enregistrer,
                  fg_color="#4CAF50", hover_color="#45a049", height=40).pack(pady=15)

def creer_categorie():
    win = ctk.CTkToplevel(app)
    win.title("📁 Nouvelle catégorie")
    win.geometry("320x160")
    win.transient(app)
    win.grab_set()
    x = app.winfo_rootx() + 150
    y = app.winfo_rooty() + 100
    win.geometry(f"320x160+{x}+{y}")

    ctk.CTkLabel(win, text="Nom de la catégorie :", font=("Segoe UI", 13)).pack(pady=(20, 5))
    entry = ctk.CTkEntry(win, font=("Segoe UI", 13), height=35)
    entry.pack(padx=20, fill="x", pady=(0, 15))
    entry.focus()

    def valider(event=None):
        nom = entry.get().strip().title()
        if nom and nom not in categories:
            categories[nom] = []
            sauvegarder()
            rebuild_categories_bar()
            charger_categorie(nom)
        win.destroy()

    ctk.CTkButton(win, text="✅ Créer", command=valider,
                  fg_color="#4CAF50", hover_color="#45a049", height=35).pack(pady=(0, 10))
    entry.bind("<Return>", valider)

def rebuild_categories_bar():
    for widget in cat_container.winfo_children():
        widget.destroy()
    for cat in sorted(categories.keys()):
        emoji = "📌"
        if "Vidéo" in cat: emoji = "▶️"
        elif "Mail" in cat: emoji = "📧"
        elif "Achat" in cat: emoji = "🛒"
        elif "Dev" in cat or "IA" in cat: emoji = "🤖"
        elif "Outil" in cat: emoji = "🛠️"
        elif "En Ligne" in cat: emoji = "🌐"
        btn = ctk.CTkButton(
            cat_container,
            text=f"{emoji} {cat}",
            fg_color="transparent",
            hover_color="#2d2d2d",
            height=36,
            font=("Segoe UI", 13),
            command=lambda c=cat: charger_categorie(c)
        )
        btn.pack(side="left", padx=5)

def charger_categorie(cat, use_favicons=False):
    global categorie_active
    categorie_active = cat
    titre_label.configure(text=f"{cat} — Sites web")

    for widget in content_frame.winfo_children():
        widget.destroy()

    if cat not in categories:
        ctk.CTkLabel(content_frame, text="❌ Catégorie introuvable.", text_color="red").pack(pady=40)
        return

    if not categories[cat]:
        ctk.CTkLabel(content_frame, text="📭 Cette catégorie est vide.", 
                    font=("Segoe UI", 14, "italic"), text_color="gray").pack(pady=(40, 10))
        ctk.CTkButton(
            content_frame,
            text="❌ Supprimer cette catégorie",
            fg_color="#E53935",
            hover_color="#C62828",
            height=36,
            font=("Segoe UI", 13, "bold"),
            command=lambda c=cat: supprimer_categorie(c)
        ).pack(pady=10)
        return

    emoji_map = {
        "Vidéo": "▶️", "Mail": "📧", "Achat": "🛒", "Dev": "🤖",
        "Outil": "🛠️", "En Ligne": "🌐", "Traduction": "🌍",
        "Site Perso": "🔒", "Test": "🧪"
    }
    emoji_cat = "📌"
    for cle, em in emoji_map.items():
        if cle in cat:
            emoji_cat = em
            break

    for idx, site in enumerate(categories[cat]):
        if len(site) < 2:
            continue
        titre = site[0]
        url = site[1]
        icone_path = site[2] if len(site) >= 3 else ""

        ligne = ctk.CTkFrame(content_frame, fg_color="#2a2a2a", corner_radius=8)
        ligne.pack(fill="x", padx=10, pady=6)

        # 🔹 ICÔNE : locale → dossier favicons → favicon sync → emoji
        icone_obj = None
        if icone_path:
            icone_obj = charger_icone_local(icone_path, size=(24, 24))
        if not isinstance(icone_obj, ctk.CTkImage):
            from urllib.parse import urlparse
            try:
                domaine = urlparse(url).netloc.lower()
                if domaine.startswith("www."): domaine = domaine[4:]
                chemin_fav = os.path.join("favicons", f"{domaine}.png")
                if os.path.isfile(chemin_fav):
                    icone_obj = charger_icone_local(chemin_fav, size=(24, 24))
                elif use_favicons:
                    icone_obj = get_favicon_sync(domaine, size=(24, 24))
            except:
                pass
        if not isinstance(icone_obj, ctk.CTkImage):
            icone_obj = emoji_cat

        if isinstance(icone_obj, ctk.CTkImage):
            label = ctk.CTkLabel(ligne, text=f" {titre}", image=icone_obj, compound="left",
                                font=("Segoe UI", 14, "bold"))
        else:
            label_text = f"{icone_obj}  {titre}"
            label = ctk.CTkLabel(ligne, text=label_text, font=("Segoe UI", 14, "bold"))
        label.pack(side="left", padx=15, pady=8)

        ctk.CTkButton(ligne, text="Ouvrir", width=90, height=32,
                      fg_color="#4CAF50", hover_color="#45a049",
                      font=("Segoe UI", 12, "bold"),
                      command=lambda u=url: ouvrir_site(u)).pack(side="right", padx=15, pady=8)

        ctk.CTkButton(ligne, text="🗑️", width=30, height=30,
                      fg_color="transparent", hover_color="#e53935",
                      command=lambda c=cat, i=idx: supprimer_site(c, i)).pack(side="right", padx=(0,8))

# === INTERFACE ===
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=1)

# Barre du haut
menu_bar = ctk.CTkFrame(app, fg_color="#1a1a1a", height=50)
menu_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
menu_bar.grid_propagate(False)

ctk.CTkLabel(menu_bar, text="🌐 Mes Sites", font=("Segoe UI", 16, "bold")).pack(side="left", padx=15)

cat_scroll = ctk.CTkScrollableFrame(
    menu_bar,
    fg_color="transparent",
    orientation=HORIZONTAL,
    height=40
)
cat_scroll.pack(side="left", fill="x", expand=True, padx=(10, 0))

cat_container = ctk.CTkFrame(cat_scroll, fg_color="transparent")
cat_container.pack(side="left", fill="y")

rebuild_categories_bar()

ctk.CTkButton(
    menu_bar,
    text="📁 Nouvelle catégorie",
    width=160,
    height=36,
    font=("Segoe UI", 13, "bold"),
    fg_color="#FF9800",
    hover_color="#EF6C00",
    command=creer_categorie
).pack(side="right", padx=15)

# Zone principale
main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0,15))
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(2, weight=1)

# 🔹 ÉTIQUETTE DE STATUT (en haut à droite)
status_label = ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 11), height=20)
status_label.grid(row=0, column=0, sticky="e", padx=(0,15), pady=(0,5))

# Titre
titre_label = ctk.CTkLabel(main_frame, text=f"{categorie_active} — Sites web", font=("Segoe UI", 18, "bold"))
titre_label.grid(row=0, column=0, sticky="w", pady=(0,10))

# Barre d'outils
toolbar = ctk.CTkFrame(main_frame, fg_color="transparent")
toolbar.grid(row=1, column=0, sticky="ew", pady=(0,10))

ctk.CTkButton(toolbar, text="🔄 Actualiser", 
              command=lambda: charger_categorie(categorie_active),
              fg_color="#2196F3", width=100, height=34).pack(side="left")

ctk.CTkButton(toolbar, text="🖼️ Favicons", 
              command=lambda: charger_categorie(categorie_active, use_favicons=True),
              fg_color="#9C27B0", width=100, height=34).pack(side="left", padx=(10,0))

# 🔹 NOUVEAU BOUTON
ctk.CTkButton(toolbar, text="📥 Favicons", 
              command=sauvegarder_tous_les_favicons,
              fg_color="#607D8B", hover_color="#455A64",
              width=100, height=34).pack(side="left", padx=(10,0))

ctk.CTkButton(toolbar, text="➕ Site", 
              command=ajouter_site,
              fg_color="#4CAF50", width=90, height=34).pack(side="left", padx=(10,0))

ctk.CTkButton(toolbar, text="❓ Aide", 
              command=lambda: webbrowser.open(f"file:///{os.path.abspath('aide.html')}"),
              fg_color="#795548", width=80, height=34).pack(side="right")

# Zone de contenu
content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#1a1a1a", corner_radius=12)
content_frame.grid(row=2, column=0, sticky="nsew")

# === LANCEMENT ===
charger_categorie(categorie_active)
app.mainloop()