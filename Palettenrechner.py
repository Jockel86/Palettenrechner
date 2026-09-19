import streamlit as st

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
    for pl, pb in STANDARD_PALETTEN:
        if (laenge <= pl and breite <= pb) or (laenge <= pb and breite <= pl):
            passende.append(f"{pl} x {pb} mm")
    return passende

def berechne_maximale_stueckzahl(laenge_mm, breite_mm, staerke_mm, stueckzahl, dichte_material=PE_DICHTE, max_gewicht_pro_palette=1050):
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

# CSS-Injektion für echtes Umschalten von Hintergrund und Textfarben
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("Profi-Stack Planer")
st.caption("Fokus: PE-Platten (Dichte: 0.95 g/cm³) | Max. empfohlene Stapelhöhe: 1000 mm")

# Auswahl für Zuschnitt
var_zuschnitt = st.radio("Zuschnitt wählen:", ["Standard", "Individuell"])

standard_option = "2x1"
if var_zuschnitt == "Standard":
    options = list(STANDARD_MASSE.keys())
    standard_option = st.selectbox("Wähle eine Standardgröße:", options)

# Eingabefelder für individuelle oder Standardmaße
if var_zuschnitt == "Individuell":
    laenge_mm = st.number_input("Länge in mm:", min_value=1, value=2000, step=1)
    breite_mm = st.number_input("Breite in mm:", min_value=1, value=1000, step=1)
else:
    laenge_mm, breite_mm = STANDARD_MASSE[standard_option]
    st.info(f"Ausgewählte Standardmaße: Länge = {laenge_mm} mm, Breite = {breite_mm} mm")

# Session State für die Stärke initialisieren
if "staerke_val" not in st.session_state:
    st.session_state.staerke_val = 10

def update_staerke():
    auswahl = st.session_state.dropdown_staerke
    if auswahl != "Schnell-Auswahl...":
        st.session_state.staerke_val = int(auswahl)

# Stärke-Bereich aufteilen: Links das Dropdown, Rechts das Eingabefeld mit +/- Buttons
col_drop, col_input = st.columns([1, 1])

with col_drop:
    st.selectbox(
        "Standard-Stärken:", 
        ["Schnell-Auswahl...", 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100],
        key="dropdown_staerke",
        on_change=update_staerke
    )

with col_input:
    staerke_mm = st.number_input(
        "Stärke in mm:", 
        min_value=1, 
        step=1, 
        key="staerke_val"
    )

stueckzahl = st.number_input("Stückzahl:", min_value=0, value=0, step=1)
max_gewicht_pro_palette = st.number_input("Maximales Gewicht pro Palette in kg:", value=1050.0, step=50.0)

# Berechnungs-Button
if st.button("Berechnung starten", type="primary"):
    try:
        if stueckzahl <= 0:
            st.warning("Bitte gib eine Stückzahl größer als 0 ein.")
        else:
            benoetigte_paletten, stueckzahlen, gewichte, stapelhoehen = berechne_maximale_stueckzahl(
                laenge_mm, breite_mm, staerke_mm, stueckzahl, PE_DICHTE, max_gewicht_pro_palette)

            # Ermitteln, ob es einem bekannten Standardnamen entspricht
            paletten_bezeichnung = ""
            if var_zuschnitt == "Standard":
                paletten_bezeichnung = standard_option
            else:
                for name, (l, b) in STANDARD_MASSE.items():
                    if (laenge_mm == l and breite_mm == b) or (laenge_mm == b and breite_mm == l):
                        paletten_bezeichnung = name
                        break

            # Hauptausgabe mit integrierter Bezeichnung falls Standard
            if paletten_bezeichnung:
                st.markdown(f"### Du benötigst insgesamt **{benoetigte_paletten} Palette(n) {paletten_bezeichnung}**.")
            else:
                st.markdown(f"### Du benötigst insgesamt **{benoetigte_paletten} Palette(n)**.")

            # Passende Paletten / Hinweis anzeigen
            passende_pals = finde_passende_paletten(laenge_mm, breite_mm)
            if passende_pals:
                paletten_text = ", ".join(passende_pals)
                st.info(f"📦 **Verwendbare Standardpalette(n):** {paletten_text}")
            else:
                st.warning("⚠️ **Hinweis:** Bei diesen Maßen handelt es sich um Sonderformate. Gegebenenfalls sind konforme Sonderpaletten (IPPC / ISPM 15) einzuplanen.")

            st.markdown("---")

            # Zusammenfassung gruppieren
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
                st.warning("⚠️ **Logistik-Hinweis:** Mindestens eine Palette überschreitet die empfohlene maximale Stapelhöhe von 1000 mm. Bitte Handhabung und Kippsicherheit beim Transport prüfen!")

            st.markdown("---")
            st.subheader("Gewichtsauslastung & Stapelhöhe pro Palette:")

            # Dynamisch eingefärbte Fortschrittsbalken mit angepassten Farben für Hell-/Dunkelmodus
            for i in range(benoetigte_paletten):
                stueck = stueckzahlen[i]
                gesamtgewicht = round(gewichte[i], 2)
                stapelhoehe = round(stapelhoehen[i], 2)
                
                auslastung_wert = (gesamtgewicht / max_gewicht_pro_palette) * 100
                prozent = min(round(auslastung_wert, 1), 100)
                
                # HSL-Farbton: 0 (Rot/Orange) steigt an bis 120 (Sattes Grün bei 100%)
                hue = int((prozent / 100) * 120)
                
                extra_text = f" | Höhe: {stapelhoehe} mm"
                if stapelhoehe > MAX_STAPELHOEHE_MM:
                    extra_text += " ⚠️ (Über 1000 mm!)"

                st.markdown(f"""
                    <div style="margin-bottom: 12px;">
                        <div style="font-size: 14px; margin-bottom: 4px; color: {text_color};">
                            <b>Palette {i+1}:</b> {stueck} Stück ({gesamtgewicht} kg von {max_gewicht_pro_palette} kg | {prozent}%){extra_text}
                        </div>
                        <div style="background-color: {bg_bar_color}; border-radius: 4px; overflow: hidden; height: 14px; width: 100%; border: 1px solid {border_bar_color};">
                            <div style="background-color: hsl({hue}, 85%, 45%); width: {prozent}%; height: 100%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Fehler: {str(e)}")

# Signatur am Fuß der Seite
st.markdown("---")
st.markdown(f"<div style='text-align: right; color: gray; font-size: 12px;'>Jochen Vortkamp 2026</div>", unsafe_allow_html=True)
