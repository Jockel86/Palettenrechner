import streamlit as st
from datetime import datetime
import io

# --- PASSWORT-SCHUTZ ---
def check_password():
    """Gibt True zurück, wenn das Passwort korrekt eingegeben wurde."""
    def password_entered():
        if st.session_state["password"] == "1904":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Passwort aus dem State löschen
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Ersteingabe: Zeige Passwortfeld
        st.markdown("## 🪵 Profi-Stack Planer - Login")
        st.text_input("Bitte Passwort eingeben, um fortzufahren:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Falsches Passwort wurde eingegeben
        st.markdown("## 🪵 Profi-Stack Planer - Login")
        st.text_input("Bitte Passwort eingeben, um fortzufahren:", type="password", on_change=password_entered, key="password")
        st.error("😕 Das eingegebene Passwort ist leider falsch.")
        return False
    else:
        # Korrektes Passwort eingeloggt
        return True

# Wenn nicht eingeloggt, hier stoppen (App wird nicht weiter ausgeführt)
if not check_password():
    st.stop()


# --- HILFSFUNKTION FÜR PDF-GENERIERUNG ---
def generiere_fertigungsauftrag_text(laenge_mm, breite_mm, benoetigte_paletten, max_gewicht_pro_palette):
    """Erstellt den Text für den Fertigungsauftrag."""
    aktuelles_datum = datetime.now().strftime("%d.%m.%Y")
    return f"""FERTIGUNGSAUFTRAG: SONDERPALETTE
==================================================
Erstellungsdatum: {aktuelles_datum}
Ersteller: Jochen Vortkamp
Status: Dringend / Maßanfertigung

TECHNISCHE SPEZIFIKATIONEN DER SONDERPALETTE:
- Plattenformat (Länge x Breite): {laenge_mm} mm x {breite_mm} mm
- Benötigte Paletten-Anzahl: {benoetigte_paletten} Stk.
- Max. Belastungsgewicht pro Palette: {max_gewicht_pro_palette} kg
- ISPM 15 / IPPC-Standard: [ ] Erforderlich (Export)

PRODUKTIONS- UND QUALITÄTSCHECKLISTE:
[ ] Holz-/Materialzuschnitt nach Maßangabe vorbereiten
[ ] Untergrund- und Klötzchenkonstruktion montieren
[ ] Maßhaltigkeit prüfen (Toleranz max. +- 2 mm)
[ ] Tragfähigkeit auf mindestens {max_gewicht_pro_palette} kg prüfen / freigeben
[ ] Kennzeichnung / Stempelung anbringen

--------------------------------------------------
Generiert automatisch über den Profi-Stack Planer.
"""


# --- AB HIER BEGINNT DAS EIGENTLICHE TOOL ---

# Feste Dichte für PE (Polyethylen) in g/cm³ bzw. kg/dm³
PE_DICHTE = 0.95
MAX_STAPELHOEHE_MM = 1000  # Maximale empfohlene Stapelhöhe für das Handling

# Mapping für Standard-Namen und deren Maße
STANDARD_MASSE = {
    "2x1": (2050, 1020), 
    "2x1.25": (2030, 1250), 
    "3x1": (3050, 1020), 
    "3x1.25": (3050, 1250), 
    "3x2": (3050, 2080)
}

# Erweiterte Liste aller Standardpaletten für die Sonderformat-Prüfung
STANDARD_PALETTEN = [
    (1100, 1100), (1200, 800), (1100, 1300), 
    (2050, 1020), (2050, 1250), (3050, 1020), (3050, 1250), 
    (4050, 1020), (5050, 1020), (6050, 500), (6050, 1020), 
    (3050, 2080), (4050, 2050), (5050, 2050)
]

def finde_passende_paletten(laenge, breite):
    passende = []
    # Toleranz: Palette darf maximal 10 cm (100 mm) länger oder breiter sein als der Zuschnitt
    toleranz_mm = 100
    
    for pl, pb in STANDARD_PALETTEN:
        # Normal ausgerichtet
        normal_passt = (laenge <= pl) and (breite <= pb) and ((pl - laenge) <= toleranz_mm) and ((pb - breite) <= toleranz_mm)
        # Gedreht ausgerichtet
        gedreht_passt = (laenge <= pb) and (breite <= pl) and ((pb - laenge) <= toleranz_mm) and ((pl - breite) <= toleranz_mm)
        
        if normal_passt or gedreht_passt:
            passende.append(f"{pl} x {pb} mm")
    return passende

def berechne_maximale_stueckzahl(laenge_mm, breite_mm, staerke_mm, stueckzahl, dichte_material=PE_DICHTE, max_gewicht_pro_palette=1100):
    laenge_meter = laenge_mm / 1000
    breite_meter = breite_mm / 1000
    staerke_meter = staerke_mm / 1000  # mm zu Meter für die Volumenberechnung

    volumen_pro_stueck = laenge_meter * breite_meter * staerke_meter
    dichte_kg_m3 = dichte_material * 1000  # Umrechnung in kg/m³
    
    gewicht_pro_stueck = volumen_pro_stueck * dichte_kg_m3

    if gewicht_pro_stueck <= 0 or stueckzahl <= 0:
        return 0, [], [], []

    max_stueckzahl_pro_palette = int(max_gewicht_pro_palette / gewicht_pro_stueck)
    if max_stueckzahl_pro_palette <= 0:
        max_stueckzahl_pro_palette = 1

    benoetigte_paletten = (stueckzahl + max_stueckzahl_pro_palette - 1) // max_stueckzahl_pro_palette

    stueckzahl_pro_palette = stueckzahl // benoetigte_paletten
    verbleibende_stueckzahl = stueckzahl % benoetigte_paletten

    stueckzahlen = [stueckzahl_pro_palette] * benoetigte_paletten

    for i in range(verbleibende_stueckzahl):
        stueckzahlen[i] += 1

    gewichte = []
    stapelhoehen = []

    for stueck in stueckzahlen:
        gesamtgewicht_pro_palette = gewicht_pro_stueck * stueck
        stapelhoehe_pro_palette = staerke_mm * stueck
        gewichte.append(gesamtgewicht_pro_palette)
        stapelhoehen.append(stapelhoehe_pro_palette)

    return benoetigte_paletten, stueckzahlen, gewichte, stapelhoehen

# Callback-Funktion, wenn im Schnellwahl-Dropdown eine Stärke gewählt wird
def setze_standard_staerke():
    auswahl = st.session_state.schnell_staerke
    if auswahl != "Standard wählen...":
        st.session_state.staerke_val = int(auswahl)

# Reset-Funktion für den Zurücksetzen-Button
def reset_form():
    st.session_state.var_zuschnitt = "Standard"
    st.session_state.standard_option = "2x1"
    st.session_state.laenge_mm = 2000
    st.session_state.breite_mm = 1000
    st.session_state.staerke_val = 10
    st.session_state.schnell_staerke = "Standard wählen..."
    st.session_state.stueckzahl = 0
    st.session_state.max_gewicht_pro_palette = 1100.0

# Session State Initialisierung
if "var_zuschnitt" not in st.session_state:
    st.session_state.var_zuschnitt = "Standard"
if "standard_option" not in st.session_state:
    st.session_state.standard_option = "2x1"
if "laenge_mm" not in st.session_state:
    st.session_state.laenge_mm = 2000
if "breite_mm" not in st.session_state:
    st.session_state.breite_mm = 1000
if "staerke_val" not in st.session_state:
    st.session_state.staerke_val = 10
if "schnell_staerke" not in st.session_state:
    st.session_state.schnell_staerke = "Standard wählen..."
if "stueckzahl" not in st.session_state:
    st.session_state.stueckzahl = 0
if "max_gewicht_pro_palette" not in st.session_state:
    st.session_state.max_gewicht_pro_palette = 1100.0

# Sidebar für Einstellungen / Design-Modus
st.sidebar.header("Darstellung")
theme_mode = st.sidebar.radio("Modus wählen:", ["Dunkelmodus", "Hellmodus"])

# CSS-Styling je nach gewähltem Modus definieren
if theme_mode == "Dunkelmodus":
    bg_color = "#0e1117"
    text_color = "#FAFAFA"
    bg_bar_color = "#262730"
    border_bar_color = "#41424C"
    sidebar_bg = "#262730"
else:
    bg_color = "#FFFFFF"
    text_color = "#31333F"
    bg_bar_color = "#E0E2EC"
    border_bar_color = "#D1D3D9"
    sidebar_bg = "#F0F2F6"

# CSS-Injektion für Farb-Anpassungen & kompaktere Abstände
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    /* Grüner Button für Berechnung starten */
    div.stButton > button[kind="primary"] {{
        background-color: #28a745;
        border-color: #28a745;
        color: white;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: #218838;
        border-color: #1e7e34;
    }}
    /* Roter Button für Reset */
    div.stButton > button:not([kind="primary"]) {{
        background-color: #dc3545;
        border-color: #dc3545;
        color: white;
    }}
    div.stButton > button:not([kind="primary"]):hover {{
        background-color: #c82333;
        border-color: #bd2130;
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

# Kompakte Überschrift statt großem Banner
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        <span style="font-size: 24px;">🪵</span>
        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: {text_color};">Profi-Stack Planer</h2>
        <span style="font-size: 12px; opacity: 0.6; margin-left: auto;">PE (0.95 g/cm³) &bull; Max. 1000 mm</span>
    </div>
""", unsafe_allow_html=True)

# Auswahl für Zuschnitt
var_zuschnitt = st.radio("Zuschnitt wählen:", ["Standard", "Individuell"], key="var_zuschnitt", horizontal=True)

if var_zuschnitt == "Standard":
    options = list(STANDARD_MASSE.keys())
    standard_option = st.selectbox("Wähle eine Standardgröße:", options, key="standard_option")
    laenge_mm, breite_mm = STANDARD_MASSE[standard_option]
    st.caption(f"Ausgewählte Standardmaße: Länge = {laenge_mm} mm, Breite = {breite_mm} mm")
else:
    col_l, col_b = st.columns(2)
    with col_l:
        laenge_mm = st.number_input("Länge in mm:", min_value=1, step=1, key="laenge_mm")
    with col_b:
        breite_mm = st.number_input("Breite in mm:", min_value=1, step=1, key="breite_mm")
    
    # Prüfung mit neuer Toleranz (max. 10 cm größer/breiter)
    passende_pals_check = finde_passende_paletten(laenge_mm, breite_mm)
    if not passende_pals_check:
        st.warning("⚠️ **Hinweis:** Keine passende Standardpalette innerhalb der 10-cm-Toleranz gefunden. Es müssen Sonderpaletten eingeplant werden!")

# Stärke nebeneinander: Links die Schnell-Auswahl für Standards, Rechts das Haupt-Zahlenfeld mit +/-
col_schnell, col_zahl = st.columns([1, 1])

with col_schnell:
    st.selectbox(
        "Standard-Stärken wählen:", 
        ["Standard wählen...", 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100],
        key="schnell_staerke",
        on_change=setze_standard_staerke
    )

with col_zahl:
    staerke_mm = st.number_input(
        "Plattenstärke in mm:", 
        min_value=1, 
        max_value=500,
        step=1, 
        key="staerke_val"
    )

col_stk, col_gew = st.columns(2)
with col_stk:
    stueckzahl = st.number_input("Stückzahl:", min_value=0, step=1, key="stueckzahl")
with col_gew:
    max_gewicht_pro_palette = st.number_input("Max. Gewicht pro Palette (kg):", step=50.0, key="max_gewicht_pro_palette")

st.markdown("")  # Kleiner Abstand

# Buttons nebeneinander: Berechnung starten (Grün) & Neue Berechnung / Reset (Rot)
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    berechnen_gedrueckt = st.button("Berechnung starten", type="primary", use_container_width=True)
with col_btn2:
    st.button("Neue Berechnung (Reset)", on_click=reset_form, use_container_width=True)

# Berechnungs-Logik ausführen, wenn Button gedrückt wurde
if berechnen_gedrueckt:
    try:
        if stueckzahl <= 0:
            st.warning("Bitte gib eine Stückzahl größer als 0 ein.")
        else:
            benoetigte_paletten, stueckzahlen, gewichte, stapelhoehen = berechne_maximale_stueckzahl(
                laenge_mm, breite_mm, staerke_mm, stueckzahl, PE_DICHTE, max_gewicht_pro_palette)

            paletten_bezeichnung = ""
            if var_zuschnitt == "Standard":
                paletten_bezeichnung = standard_option
            else:
                for name, (l, b) in STANDARD_MASSE.items():
                    if (laenge_mm == l and breite_mm == b) or (laenge_mm == b and breite_mm == l):
                        paletten_bezeichnung = name
                        break

            st.markdown("---")
            if paletten_bezeichnung:
                st.markdown(f"### Du benötigst insgesamt **{benoetigte_paletten} Palette(n) {paletten_bezeichnung}**.")
            else:
                st.markdown(f"### Du benötigst insgesamt **{benoetigte_paletten} Palette(n)**.")

            passende_pals = finde_passende_paletten(laenge_mm, breite_mm)
            
            if not passende_pals:
                st.warning("⚠️ **Logistik-Hinweis:** Keine passende Standardpalette innerhalb der 10-cm-Toleranz. Sonderpaletten erforderlich!")
                
                auftrag_text = generiere_fertigungsauftrag_text(laenge_mm, breite_mm, benoetigte_paletten, max_gewicht_pro_palette)
                datei_name = f"Fertigungsauftrag_Sonderpalette_{laenge_mm}x{breite_mm}mm.txt"
                
                st.download_button(
                    label="📥 Fertigungsauftrag als Datei herunterladen",
                    data=auftrag_text,
                    file_name=datei_name,
                    mime="text/plain",
                    type="secondary"
                )

            paletten_ergebnisse = {}
            fuer_hoehen_warnung = False
            
            for i in range(benoetigte_paletten):
                stueck = stueckzahlen[i]
                gesamtgewicht = round(gewichte[i], 2)
                stapelhoehe = round(stapelhoehen[i], 2)
                
                if stapelhoehe > MAX_STAPELHOEHE_MM:
                    fuer_hoehen_warnung = True

                key = f"{stueck} Stück"
                if key in paletten_ergebnisse:
                    paletten_ergebnisse[key]["count"] += 1
                else:
                    paletten_ergebnisse[key] = {"count": 1, "gewicht": gesamtgewicht, "hoehe": stapelhoehe}

            for key, value in paletten_ergebnisse.items():
                hoehen_hinweis = " ⚠️ *(Stapelhöhe > 1000 mm!)*" if value['hoehe'] > MAX_STAPELHOEHE_MM else ""
                st.write(f"• **{value['count']} Palette(n)** mit {key} (*{value['gewicht']} kg / **{value['hoehe']} mm** hoch*){hoehen_hinweis}")

            if fuer_hoehen_warnung:
                st.warning("⚠️ **Logistik-Hinweis:** Mindestens eine Palette überschreitet die empfohlene maximale Stapelhöhe von 1000 mm.")

            st.markdown("---")
            st.subheader("Gewichtsauslastung & Stapelhöhe pro Palettentyp:")

            # Zusammengefasste Ansicht der Auslastung (Gruppierung nach identischem Packmuster)
            zusammenfassung = {}
            for i in range(benoetigte_paletten):
                stueck = stueckzahlen[i]
                gesamtgewicht = round(gewichte[i], 2)
                stapelhoehe = round(stapelhoehen[i], 2)
                
                pack_key = (stueck, gesamtgewicht, stapelhoehe)
                if pack_key in zusammenfassung:
                    zusammenfassung[pack_key]["anzahl"] += 1
                else:
                    zusammenfassung[pack_key] = {"anzahl": 1, "gewicht": gesamtgewicht, "hoehe": stapelhoehe, "stueck": stueck}

            for pack_key, data in zusammenfassung.items():
                anzahl = data["anzahl"]
                stueck = data["stueck"]
                gesamtgewicht = data["gewicht"]
                stapelhoehe = data["hoehe"]
                
                auslastung_wert = (gesamtgewicht / max_gewicht_pro_palette) * 100
                prozent = min(round(auslastung_wert, 1), 100)
                
                hue = int((prozent / 100) * 120)
                
                extra_text = f" | Höhe: {stapelhoehe} mm"
                if stapelhoehe > MAX_STAPELHOEHE_MM:
                    extra_text += " ⚠️ (Über 1000 mm!)"

                paletten_label = f"{anzahl}x Palette" if anzahl > 1 else "1x Palette"

                st.markdown(f"""
                    <div style="margin-bottom: 15px;">
                        <div style="font-size: 13px; margin-bottom: 3px; color: {text_color};">
                            <b>{paletten_label}:</b> je {stueck} Stück ({gesamtgewicht} kg von {max_gewicht_pro_palette} kg | {prozent}%){extra_text}
                        </div>
                        <div style="background-color: {bg_bar_color}; border-radius: 4px; overflow: hidden; height: 10px; width: 100%; border: 1px solid {border_bar_color};">
                            <div style="background-color: hsl({hue}, 85%, 45%); width: {prozent}%; height: 100%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Fehler: {str(e)}")

# Signatur am Fuß der Seite
st.markdown("---")
st.markdown(f"<div style='text-align: right; color: gray; font-size: 11px;'>Jochen Vortkamp 2026</div>", unsafe_allow_html=True)
