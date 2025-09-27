import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

st.title("Nested Pie Chart: Nutzung & Raum")

csv_file = st.file_uploader("CSV-Datei mit Raumdaten auswählen", type="csv")

if csv_file:
    df = pd.read_csv(csv_file)

    # Summiere Flächen nach Raumtyp/Nutzung
    usage_grouped = df.groupby("Nutzungsart")["Fläche_soll_m2"].sum()

    # Farben für Typen (äußerer Ring)
    usage_types = list(usage_grouped.index)
    base_colors = plt.cm.tab20.colors[:len(usage_types)]

    # Daten für Innenring (Räume)
    room_labels = df["Raumname"]
    room_usages = df["Nutzungsart"]
    room_flächen = df["Fläche_soll_m2"]
    # jedem Raum-Typ zugeordnete Grundfarbe, pro Raum schattieren
    room_colors = []

    for i, usage in enumerate(room_usages):
        base = mcolors.to_rgb(base_colors[usage_types.index(usage)])
        # Schattierung je nach Reihenfolge
        factor = 0.3 + 0.7 * (i + 1) / len(df)
        shade = tuple(factor * c for c in base)
        room_colors.append(shade)

    fig, ax = plt.subplots(figsize=(8, 8))
    # Äußerer Ring: Nutzungstyp (Raumtyp)
    wedges_outer, _ = ax.pie(
        usage_grouped,
        radius=1,
        labels=usage_types,
        colors=base_colors,
        wedgeprops=dict(width=0.3, edgecolor='w'),
        startangle=90,
        autopct='%1.1f%%'
    )
    # Innerer Ring: Einzelräume, Schattierung nach Typ
    wedges_inner, _ = ax.pie(
        room_flächen,
        radius=0.7,
        labels=room_labels,
        colors=room_colors,
        wedgeprops=dict(width=0.3, edgecolor='w'),
        startangle=90
    )
    ax.set(aspect="equal", title="Nested Pie Chart: Nutzung & einzelne Räume")
    st.pyplot(fig)
else:
    st.info("Bitte eine CSV-Datei auswählen, um das Diagramm zu sehen.")
