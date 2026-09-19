import streamlit as st

# Feste Dichte für PE (Polyethylen) in g/cm³ bzw. kg/dm³
PE_DICHTE = 0.95
MAX_STAPELHOEHE_MM = 1000  # Maximale empfohlene Stapelhöhe für das Handling

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

# Streamlit UI
st.title("JV PalettenMaster")
st.caption("Fokus: PE-Platten (Dichte: 0.95 g/cm³) | Max. empfohlene Stapelhöhe: 1000 mm")

# Auswahl für Zuschnitt
var_zuschnitt = st.radio("Zuschnitt wählen:", ["Standard", "Individuell"])

standard_option = "2x1"
if var_zuschnitt == "Standard":
    options = ["2x1", "2x1.25", "3x1", "3x1.25", "3x2"]
    standard_option = st.selectbox("Wähle eine Standardgröße:", options)

# Eingabefelder für individuelle oder Standardmaße
if var_zuschnitt == "Individuell":
    laenge_mm = st.number_input("Länge in mm:", min_value=1, value=2000, step=1)
    breite_mm = st.number_input("Breite in mm:", min_value=1, value=1000, step=1)
else:
    standard_masse = {
        "2x1": (2000, 1000), 
        "2x1.25": (2000, 1250), 
        "3x1": (3000, 1000), 
        "3x1.25": (3000, 1250), 
        "3x2": (3000, 2000)
    }
    laenge_mm, breite_mm = standard_masse[standard_option]
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

            st.markdown(f"### Du benötigst insgesamt **{benoetigte_paletten} Palette(n)**.")
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

            # Dynamisch eingefärbte Fortschrittsbalken (je näher an 100%, desto grüner)
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
                        <div style="font-size: 14px; margin-bottom: 4px; color: #FAFAFA;">
                            <b>Palette {i+1}:</b> {stueck} Stück ({gesamtgewicht} kg von {max_gewicht_pro_palette} kg | {prozent}%){extra_text}
                        </div>
                        <div style="background-color: #262730; border-radius: 4px; overflow: hidden; height: 14px; width: 100%; border: 1px solid #41424C;">
                            <div style="background-color: hsl({hue}, 85%, 45%); width: {prozent}%; height: 100%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            if laenge_mm > 3100 or breite_mm > 1280 or laenge_mm < 2000 or breite_mm < 1000:
                st.markdown("\n⚠️ **Hinweis:** Die Abmessungen könnten Sonderpaletten erfordern. Diese müssen evtl. den IPPC-Standard haben.")

    except Exception as e:
        st.error(f"Fehler: {str(e)}")

# Signatur am Fuß der Seite
st.markdown("---")
st.markdown("<div style='text-align: right; color: gray; font-size: 12px;'>J.Vortkamp 2024</div>", unsafe_allow_html=True)
