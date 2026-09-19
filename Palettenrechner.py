import streamlit as st

def berechne_maximale_stueckzahl(laenge_mm, breite_mm, staerke_mm, stueckzahl, max_gewicht_pro_palette=1050):
    laenge_meter = laenge_mm / 1000
    breite_meter = breite_mm / 1000
    staerke_meter = staerke_mm / 1  # 1-zu-1 aus dem Original übernommen

    volumen_pro_stueck = laenge_meter * breite_meter * staerke_meter
    dichte_material = 1  # kg pro Kubikmeter (Materialdichte)
    gewicht_pro_stueck = volumen_pro_stueck * dichte_material

    max_stueckzahl_pro_palette = int(max_gewicht_pro_palette / gewicht_pro_stueck)
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
st.title("Palettenrechner")

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
    # Voreinstellungen für Standardmaße gemäß der Berechnungslogik im Original
    standard_masse = {
        "2x1": (2000, 1000), 
        "2x1.25": (2000, 1250), 
        "3x1": (3000, 1000), 
        "3x1.25": (3000, 1250), 
        "3x2": (3000, 2000)
    }
    laenge_mm, breite_mm = standard_masse[standard_option]
    st.info(f"Ausgewählte Standardmaße: Länge = {laenge_mm} mm, Breite = {breite_mm} mm")

staerke_mm = st.number_input("Stärke in mm:", min_value=1, value=10, step=1)
stueckzahl = st.number_input("Stückzahl:", min_value=1, value=100, step=1)
max_gewicht_pro_palette = st.number_input("Maximales Gewicht pro Palette in kg:", value=1050.0, step=50.0)

# Berechnungs-Button
if st.button("Berechnung starten", type="primary"):
    try:
        benoetigte_paletten, stueckzahlen, gewichte, stapelhoehen = berechne_maximale_stueckzahl(
            laenge_mm, breite_mm, staerke_mm, stueckzahl, max_gewicht_pro_palette)

        ergebnis_text = f"Du benötigst für deine Berechnung **{benoetigte_paletten} Palette(n)**.\n\n"

        paletten_ergebnisse = {}
        for i in range(benoetigte_paletten):
            stueck = stueckzahlen[i]
            gesamtgewicht = round(gewichte[i], 2)
            stapelhoehe = round(stapelhoehen[i], 2)
            key = f"{stueck} Stück"
            if key in paletten_ergebnisse:
                paletten_ergebnisse[key]["count"] += 1
            else:
                paletten_ergebnisse[key] = {"count": 1, "gewicht": gesamtgewicht, "hoehe": stapelhoehe}

        for key, value in paletten_ergebnisse.items():
            ergebnis_text += f"- **{value['count']} Palette(n)** mit {key} (*{value['gewicht']} kg / {value['hoehe']} mm hoch*)\n"

        if laenge_mm > 3100 or breite_mm > 1280 or laenge_mm < 2000 or breite_mm < 1000:
            ergebnis_text += "\n\n⚠️ **Hinweis:** Die Abmessungen könnten Sonderpaletten erfordern. Diese müssen evtl. den IPPC-Standard haben."

        st.markdown(ergebnis_text)

    except Exception as e:
        st.error(f"Fehler: {str(e)}")

# Signatur am Fuß der Seite
st.markdown("---")
st.markdown("<div style='text-align: right; color: gray; font-size: 12px;'>J.Vortkamp 2024</div>", unsafe_allow_html=True)