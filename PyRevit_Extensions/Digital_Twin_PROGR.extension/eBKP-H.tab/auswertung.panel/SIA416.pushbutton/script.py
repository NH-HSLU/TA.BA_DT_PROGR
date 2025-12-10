# -*- coding: utf-8 -*-
"""
SIA 416 Flaechen- und Volumenberechnung
Berechnet Gebaeudekennzahlen nach Schweizer Norm SIA 416
"""

__title__ = "SIA 416\nKennzahlen"
__author__ = "TA.BA_DT_PROGR_Gruppe21"
__doc__ = "Berechnet Volumen und Flaechen nach SIA 416 und exportiert sie nach Excel/CSV"

from pyrevit import revit, DB, forms, script
import csv
import codecs
from datetime import datetime
from collections import defaultdict

# Output fuer Meldungen
output = script.get_output()
doc = revit.doc


# ========================================
# HILFSFUNKTIONEN - UNIT CONVERSION
# ========================================

def round_area_m2(value_in_sqft):
    """Konvertiert Flaeche von sqft zu m2 mit 2 Kommastellen"""
    if value_in_sqft is None or value_in_sqft == 0:
        return 0.0
    return round(value_in_sqft * 0.092903, 2)


def round_volume_m3(value_in_cuft):
    """Konvertiert Volumen von cuft zu m3 mit 3 Kommastellen"""
    if value_in_cuft is None or value_in_cuft == 0:
        return 0.0
    return round(value_in_cuft * 0.0283168, 3)


def round_length_m(value_in_feet):
    """Konvertiert Laenge von feet zu m mit 2 Kommastellen"""
    if value_in_feet is None or value_in_feet == 0:
        return 0.0
    return round(value_in_feet * 0.3048, 2)


# ========================================
# SIA 416 KATEGORISIERUNG
# ========================================

def categorize_room_sia416(room_name, room_number=""):
    """
    Kategorisiert einen Raum nach SIA 416 basierend auf Namen/Nummer

    Returns:
        str: Eine der Kategorien: HNF, NNF, VF, FF, AGF oder ""

    SIA 416 Kategorien:
    - HNF (Hauptnutzflaeche): Wohnen, Buero, Verkauf, Gastronomie
    - NNF (Nebennutzflaeche): Lager, Technik, Keller
    - VF (Verkehrsflaeche): Flure, Treppen, Aufzuege
    - FF (Funktionsflaeche): WC, Bad, Kueche (in VF/NF integriert)
    - AGF (Aussengeschossflaeche): Balkone, Loggias, Terrassen
    """
    name_lower = room_name.lower() if room_name else ""

    # Hauptnutzflaeche (HNF) - Kernnutzung
    hnf_keywords = [
        "wohn", "schlaf", "buero", "buero", "office", "arbeits",
        "verkauf", "laden", "shop", "gastronomie", "restaurant",
        "unterricht", "seminar", "konferenz", "sitzung", "besprechung"
    ]
    for keyword in hnf_keywords:
        if keyword in name_lower:
            return "HNF"

    # Verkehrsflaeche (VF)
    vf_keywords = [
        "flur", "korridor", "gang", "treppe", "treppenhaus",
        "aufzug", "lift", "eingang", "foyer", "halle", "diele"
    ]
    for keyword in vf_keywords:
        if keyword in name_lower:
            return "VF"

    # Nebennutzflaeche (NNF)
    nnf_keywords = [
        "lager", "abstellraum", "abstell", "keller", "archive",
        "hauswirtschaft", "waschkueche", "waschkueche", "putzraum",
        "garderobe", "umkleide"
    ]
    for keyword in nnf_keywords:
        if keyword in name_lower:
            return "NNF"

    # Funktionsflaeche (FF) - Technik
    ff_keywords = [
        "technik", "heizung", "hvac", "klima", "lueftung", "lueftung",
        "elektro", "server", "it-raum", "maschinenraum"
    ]
    for keyword in ff_keywords:
        if keyword in name_lower:
            return "FF"

    # Aussengeschossflaeche (AGF)
    agf_keywords = [
        "balkon", "loggia", "terrasse", "laubengang", "veranda"
    ]
    for keyword in agf_keywords:
        if keyword in name_lower:
            return "AGF"

    # WC/Bad als Funktionsflaeche
    if "wc" in name_lower or "bad" in name_lower or "toilet" in name_lower or "dusch" in name_lower:
        return "FF"

    # Kueche kann HNF oder FF sein - hier als FF
    if "kueche" in name_lower or "kueche" in name_lower or "kitchen" in name_lower:
        return "FF"

    # Default: Hauptnutzflaeche (wenn unklar)
    return "HNF"


# ========================================
# DATENSAMMLUNG
# ========================================

def collect_rooms():
    """Sammelt alle Raeume aus dem Modell"""
    rooms = DB.FilteredElementCollector(doc)\
        .OfCategory(DB.BuiltInCategory.OST_Rooms)\
        .WhereElementIsNotElementType()\
        .ToElements()

    room_data = []

    for room in rooms:
        # Skip platzierte aber nicht begrenzte Raeume
        if room.Area == 0:
            continue

        # Raum-Informationen
        room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or "Unbenannt"
        room_number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or ""

        # Flaeche und Volumen
        # Flaeche direkt ueber room.Area (bereits in sqft)
        area_sqft = room.Area
        area_m2 = round_area_m2(area_sqft)

        # Volumen berechnen: Flaeche x Hoehe
        # Versuche zuerst ueber Parameter
        volume_cuft = 0
        volume_param = room.get_Parameter(DB.BuiltInParameter.ROOM_VOLUME)
        if volume_param and volume_param.HasValue:
            volume_cuft = volume_param.AsDouble()

        # Wenn kein Volumen gefunden, berechne aus Flaeche x Hoehe
        if volume_cuft == 0 or volume_cuft is None:
            # Hole Raumhoehe
            height_ft = 0

            # Methode 1: Aus ROOM_HEIGHT Parameter
            height_param = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT)
            if height_param and height_param.HasValue:
                height_ft = height_param.AsDouble()

            # Methode 2: Aus unbegrenzter Hoehe (falls begrenzt)
            if height_ft == 0:
                height_param_unbounded = room.get_Parameter(DB.BuiltInParameter.ROOM_UPPER_OFFSET)
                if height_param_unbounded and height_param_unbounded.HasValue:
                    height_ft = height_param_unbounded.AsDouble()

            # Methode 3: Aus Geschosshoehe (Level to Level)
            if height_ft == 0:
                try:
                    level = doc.GetElement(room.LevelId)
                    if level:
                        # Finde naechsthoehere Ebene
                        all_levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
                        sorted_levels = sorted(all_levels, key=lambda l: l.Elevation)

                        current_elevation = level.Elevation
                        for i, lv in enumerate(sorted_levels):
                            if lv.Id == level.Id and i < len(sorted_levels) - 1:
                                next_level = sorted_levels[i + 1]
                                height_ft = next_level.Elevation - current_elevation
                                break

                        # Fallback: Standard-Geschosshoehe 3m = 9.84ft
                        if height_ft == 0:
                            height_ft = 0#9.84
                except:
                    # Fallback: Standard-Geschosshoehe 3m
                    height_ft = 0#9.84

            # Berechne Volumen: Flaeche x Hoehe
            volume_cuft = area_sqft * height_ft

        volume_m3 = round_volume_m3(volume_cuft)

        # Ebene
        level_id = room.LevelId
        level = doc.GetElement(level_id)
        level_name = level.Name if level else "Unbekannt"

        # SIA 416 Kategorisierung
        sia_category = categorize_room_sia416(room_name, room_number)

        room_data.append({
            'name': room_name,
            'number': room_number,
            'level': level_name,
            'area_m2': area_m2,
            'volume_m3': volume_m3,
            'sia_category': sia_category
        })

    return room_data


def collect_walls():
    """Sammelt alle Waende fuer Konstruktionsflaechenberechnung"""
    walls = DB.FilteredElementCollector(doc)\
        .OfCategory(DB.BuiltInCategory.OST_Walls)\
        .WhereElementIsNotElementType()\
        .ToElements()

    wall_data = []

    for wall in walls:
        try:
            # Wandlaenge
            length_param = wall.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH)
            length_ft = length_param.AsDouble() if length_param else 0
            length_m = round_length_m(length_ft)

            # Wanddicke aus WallType
            wall_type = wall.WallType
            width_ft = wall_type.Width if wall_type else 0
            width_m = round_length_m(width_ft)

            # Flaechenberechnung (Laenge x Dicke)
            area_m2 = round(length_m * width_m, 2) if length_m and width_m else 0

            # Pruefen ob Aussenwand
            is_exterior = False
            function_param = wall.get_Parameter(DB.BuiltInParameter.FUNCTION_PARAM)
            if function_param:
                function = function_param.AsInteger()
                # 0 = Interior, 1 = Exterior, 2 = Foundation, etc.
                if function == 1 or function == 2:
                    is_exterior = True

            # Wandflaeche (fuer Aussenwandberechnung)
            wall_area_param = wall.get_Parameter(DB.BuiltInParameter.HOST_AREA_COMPUTED)
            wall_area_sqft = wall_area_param.AsDouble() if wall_area_param else 0
            wall_area_m2 = round_area_m2(wall_area_sqft)

            wall_data.append({
                'length_m': length_m,
                'width_m': width_m,
                'area_m2': area_m2,
                'is_exterior': is_exterior,
                'wall_area_m2': wall_area_m2
            })

        except Exception as e:
            output.print_md("**Warnung:** Wanddaten konnten nicht gelesen werden: {}".format(str(e)))
            continue

    return wall_data


def collect_roofs_and_floors():
    """Sammelt Daecher und oberste Geschossdecken fuer Bedachungsflaeche"""
    # Daecher
    roofs = DB.FilteredElementCollector(doc)\
        .OfCategory(DB.BuiltInCategory.OST_Roofs)\
        .WhereElementIsNotElementType()\
        .ToElements()

    # Decken (oberste Ebene)
    ceilings = DB.FilteredElementCollector(doc)\
        .OfCategory(DB.BuiltInCategory.OST_Ceilings)\
        .WhereElementIsNotElementType()\
        .ToElements()

    roof_area = 0
    ceiling_area = 0

    for roof in roofs:
        area_param = roof.get_Parameter(DB.BuiltInParameter.HOST_AREA_COMPUTED)
        if area_param:
            roof_area += round_area_m2(area_param.AsDouble())

    # Hole hoechste Ebene
    levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
    if levels:
        max_elevation = max(level.Elevation for level in levels)
        top_level = [l for l in levels if l.Elevation == max_elevation][0]

        for ceiling in ceilings:
            level_id = ceiling.LevelId
            if level_id == top_level.Id:
                area_param = ceiling.get_Parameter(DB.BuiltInParameter.HOST_AREA_COMPUTED)
                if area_param:
                    ceiling_area += round_area_m2(area_param.AsDouble())

    return roof_area + ceiling_area


# ========================================
# SIA 416 BERECHNUNG
# ========================================

def calculate_sia416_metrics(room_data, wall_data, roof_area):
    """
    Berechnet alle SIA 416 Kennzahlen

    Returns:
        dict: Alle berechneten Werte
    """
    metrics = {}

    # ----------------------------------------
    # 1. GEBAEUDEVOLUMEN (GV)
    # ----------------------------------------
    total_volume = sum(r['volume_m3'] for r in room_data)
    metrics['GV'] = round(total_volume, 0)

    # ----------------------------------------
    # 2. GESCHOSSFLAECHE (GF) - Summe aller Raumflaechen
    # ----------------------------------------
    total_area = sum(r['area_m2'] for r in room_data)
    metrics['GF'] = round(total_area, 0)

    # ----------------------------------------
    # 3. KONSTRUKTIONSFLAECHE (KF) - Wandstaerken horizontal
    # ----------------------------------------
    construction_area = sum(w['area_m2'] for w in wall_data)
    metrics['KF'] = round(construction_area, 0)

    # ----------------------------------------
    # 4. NETTOGESCHOSSFLAECHE (NGF) - GF - KF
    # ----------------------------------------
    metrics['NGF'] = round(metrics['GF'] - metrics['KF'], 0)

    # ----------------------------------------
    # 5. KATEGORISIERTE FLAECHEN (VF, FF, NF, HNF, NNF, AGF)
    # ----------------------------------------
    vf_area = sum(r['area_m2'] for r in room_data if r['sia_category'] == 'VF')
    ff_area = sum(r['area_m2'] for r in room_data if r['sia_category'] == 'FF')
    hnf_area = sum(r['area_m2'] for r in room_data if r['sia_category'] == 'HNF')
    nnf_area = sum(r['area_m2'] for r in room_data if r['sia_category'] == 'NNF')
    agf_area = sum(r['area_m2'] for r in room_data if r['sia_category'] == 'AGF')

    metrics['VF'] = round(vf_area, 0)
    metrics['FF'] = round(ff_area, 0)
    metrics['HNF'] = round(hnf_area, 0)
    metrics['NNF'] = round(nnf_area, 0)
    metrics['AGF'] = round(agf_area, 0)

    # Nutzflaeche (NF) = HNF + NNF (vereinfacht)
    metrics['NF'] = round(hnf_area + nnf_area + ff_area, 0)

    # ----------------------------------------
    # 6. AUSSENWANDFLAECHE (FAW)
    # ----------------------------------------
    exterior_wall_area = sum(w['wall_area_m2'] for w in wall_data if w['is_exterior'])
    metrics['FAW'] = round(exterior_wall_area, 0)

    # ----------------------------------------
    # 7. BEDACHUNGSFLAECHE (FB)
    # ----------------------------------------
    metrics['FB'] = round(roof_area, 0)

    # ----------------------------------------
    # 8. VERHAELTNISSE (FAW/GF, FB/GF)
    # ----------------------------------------
    if metrics['GF'] > 0:
        metrics['FAW/GF'] = round(metrics['FAW'] / metrics['GF'], 2)
        metrics['FB/GF'] = round(metrics['FB'] / metrics['GF'], 2)
    else:
        metrics['FAW/GF'] = 0.0
        metrics['FB/GF'] = 0.0

    # ----------------------------------------
    # 9. GRUNDSTUECKSFLAECHEN (Placeholder - manuell eintragen)
    # ----------------------------------------
    # Diese muessen meist manuell erfasst werden, da nicht im Modell
    metrics['GSF'] = 0  # Grundstueckflaeche - manuell
    metrics['GGF'] = 0  # Gebaeudegrund flaeche - kann aus Footprint berechnet werden
    metrics['UF'] = 0   # Umgebungsflaeche = GSF - GGF
    metrics['BUF'] = 0  # Bearbeitete Umgebungsflaeche - manuell

    # Versuche GGF zu schaetzen (kleinste Geschossflaeche oder Erdgeschoss)
    # Dies ist eine Vereinfachung - in der Praxis komplexer
    if room_data:
        # Gruppiere nach Level
        level_areas = defaultdict(float)
        for room in room_data:
            level_areas[room['level']] += room['area_m2']

        if level_areas:
            # Nimm die kleinste Flaeche als GGF (meist Erdgeschoss)
            metrics['GGF'] = round(min(level_areas.values()), 0)

    return metrics


# ========================================
# CSV EXPORT
# ========================================

def export_to_csv(metrics, room_data):
    """Exportiert SIA 416 Kennzahlen nach CSV"""

    # Speicherort waehlen
    default_filename = "SIA416_Kennzahlen_{}.csv".format(
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    output_path = forms.save_file(
        file_ext='csv',
        default_name=default_filename,
        title="SIA 416 Export Speichern"
    )

    if not output_path:
        output.print_md("**Export abgebrochen.**")
        return False

    try:
        # CSV Schreiben mit UTF-8 Encoding (Python 2 kompatibel)
        # Verwende codecs fuer UTF-8 mit BOM
        f = codecs.open(output_path, 'w', 'utf-8-sig')
        writer = csv.writer(f, delimiter=';')

        # ========================================
        # TEIL 1: ZUSAMMENFASSUNG (wie im Screenshot)
        # ========================================
        writer.writerow([u'SIA 416 KENNZAHLEN'])
        writer.writerow([])

        # Gebaeudevolumen
        writer.writerow([u'Gebaeudevolumen'])
        writer.writerow([u'Kennzahl', u'Bezeichnung', u'Wert', u'Einheit', u'Anteil'])
        writer.writerow([u'GV', u'Gebaeudevolumen', metrics['GV'], u'm³', u'100%'])
        writer.writerow([])

        # Grundstuecksflaechen
        writer.writerow([u'Grundstuecksflaechen'])
        writer.writerow([u'Kennzahl', u'Bezeichnung', u'Wert', u'Einheit', u'Anteil'])

        gsf = metrics['GSF'] if metrics['GSF'] > 0 else metrics.get('GGF', 0)  # Fallback

        writer.writerow([u'GSF', u'Grundstuecksflaeche', gsf, u'm²', u'100%'])
        writer.writerow([u'GGF', u'Gebaeudegrundflaeche', metrics['GGF'], u'm²',
                       u'{}%'.format(int(metrics['GGF']/gsf*100) if gsf > 0 else 0)])
        writer.writerow([u'UF', u'Umgebungsflaeche', metrics['UF'], u'm²',
                       u'{}%'.format(int(metrics['UF']/gsf*100) if gsf > 0 else 0)])
        writer.writerow([u'BUF', u'Bearbeitete Umgebungsflaeche', metrics['BUF'], u'm²',
                       u'{}%'.format(int(metrics['BUF']/gsf*100) if gsf > 0 else 0)])
        writer.writerow([])

        # Gebaedeflaechen
        writer.writerow([u'Gebaedeflaechen'])
        writer.writerow([u'Kennzahl', u'Bezeichnung', u'Wert', u'Einheit', u'Anteil'])

        gf = metrics['GF']
        writer.writerow([u'GF', u'Geschossflaeche', gf, u'm²', u'100%'])
        writer.writerow([u'KF', u'Konstruktionsflaeche', metrics['KF'], u'm²',
                       u'{}%'.format(int(metrics['KF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'NGF', u'Nettogeschossflaeche', metrics['NGF'], u'm²',
                       u'{}%'.format(int(metrics['NGF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'VF', u'Verkehrsflaeche', metrics['VF'], u'm²',
                       u'{}%'.format(int(metrics['VF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'FF', u'Funktionsflaeche', metrics['FF'], u'm²',
                       u'{}%'.format(int(metrics['FF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'NF', u'Nutzflaeche', metrics['NF'], u'm²',
                       u'{}%'.format(int(metrics['NF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'HNF', u'Hauptnutzflaeche', metrics['HNF'], u'm²',
                       u'{}%'.format(int(metrics['HNF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'NNF', u'Nebennutzflaeche', metrics['NNF'], u'm²',
                       u'{}%'.format(int(metrics['NNF']/gf*100) if gf > 0 else 0)])
        writer.writerow([u'AGF', u'Aussengeschossflaeche', metrics['AGF'], u'm²',
                       u'{}%'.format(int(metrics['AGF']/gf*100) if gf > 0 else 0)])
        writer.writerow([])

        # Verhaeltnisse
        writer.writerow([u'Verhaeltnisse'])
        writer.writerow([u'Kennzahl', u'Bezeichnung', u'Wert'])
        writer.writerow([u'FAW/GF', u'Flaeche Aussenwand/Geschossflaeche', metrics['FAW/GF']])
        writer.writerow([u'FB/GF', u'Flaeche Bedachung Gebaeude/Geschossflaeche', metrics['FB/GF']])
        writer.writerow([])
        writer.writerow([])

        # ========================================
        # TEIL 2: RAUMDETAILS
        # ========================================
        writer.writerow([u'RAUMDETAILS'])
        writer.writerow([])
        writer.writerow([u'Raumnummer', u'Raumname', u'Ebene', u'Flaeche (m²)', u'Volumen (m³)', u'SIA 416 Kategorie'])

        for room in sorted(room_data, key=lambda x: (x['level'], x['number'])):
            writer.writerow([
                room['number'],
                room['name'],
                room['level'],
                room['area_m2'],
                room['volume_m3'],
                room['sia_category']
            ])

        # Datei schliessen
        f.close()

        output.print_md("---")
        output.print_md("# Export erfolgreich!")
        output.print_md("**Datei:** `{}`".format(output_path))

        # Frage ob Datei geoeffnet werden soll
        open_file = forms.alert(
            "Export erfolgreich abgeschlossen!\n\n"
            "Datei: {}\n\n"
            "Moechten Sie die CSV-Datei jetzt in Excel oeffnen?".format(output_path),
            title="SIA 416 Export",
            yes=True,
            no=True
        )

        if open_file:
            # Oeffne Datei mit Standard-Anwendung (Excel)
            try:
                import os
                os.startfile(output_path)
                output.print_md("**Info:** Datei wird in Excel geoeffnet...")
            except Exception as e:
                output.print_md("**Warnung:** Datei konnte nicht automatisch geoeffnet werden: {}".format(str(e)))

        return True

    except Exception as e:
        forms.alert("Fehler beim CSV-Export:\n\n{}".format(str(e)),
                   title="Export-Fehler", warn_icon=True)
        return False


# ========================================
# HAUPTFUNKTION
# ========================================

def main():
    """Hauptfunktion: SIA 416 Kennzahlen berechnen und exportieren"""

    output.print_md("# SIA 416 Kennzahlen Berechnung")
    output.print_md("---")

    # Schritt 1: Daten sammeln
    output.print_md("## Daten sammeln...")
    output.print_md("")

    output.print_md("**Status:** Sammle Raeume...")
    room_data = collect_rooms()
    output.print_md("**OK** {} Raeume gefunden".format(len(room_data)))

    output.print_md("**Status:** Sammle Waende...")
    wall_data = collect_walls()
    output.print_md("**OK** {} Waende gefunden".format(len(wall_data)))

    output.print_md("**Status:** Sammle Daecher/Decken...")
    roof_area = collect_roofs_and_floors()
    output.print_md("**OK** Dachflaeche: {} m2".format(roof_area))

    if not room_data:
        forms.alert("Keine Raeume im Modell gefunden!\n\nBitte platzieren Sie Raeume in Revit.",
                   title="SIA 416 - Fehler", warn_icon=True)
        return

    # Schritt 2: Kennzahlen berechnen
    output.print_md("")
    output.print_md("## Kennzahlen berechnen...")
    metrics = calculate_sia416_metrics(room_data, wall_data, roof_area)

    # Schritt 3: Ergebnisse anzeigen
    output.print_md("")
    output.print_md("## Ergebnisse (SIA 416)")
    output.print_md("---")

    output.print_md("### Gebaeudevolumen")
    output.print_md("- **GV** (Gebaeudevolumen): {} m3".format(metrics['GV']))
    output.print_md("")

    output.print_md("### Gebaedeflaechen")
    output.print_md("- **GF** (Geschossflaeche): {} m2".format(metrics['GF']))
    output.print_md("- **KF** (Konstruktionsflaeche): {} m2 ({}%)".format(
        metrics['KF'], int(metrics['KF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("- **NGF** (Nettogeschossflaeche): {} m2 ({}%)".format(
        metrics['NGF'], int(metrics['NGF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("")

    output.print_md("### Kategorisierte Flaechen")
    output.print_md("- **VF** (Verkehrsflaeche): {} m2 ({}%)".format(
        metrics['VF'], int(metrics['VF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("- **FF** (Funktionsflaeche): {} m2 ({}%)".format(
        metrics['FF'], int(metrics['FF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("- **NF** (Nutzflaeche): {} m2 ({}%)".format(
        metrics['NF'], int(metrics['NF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("- **HNF** (Hauptnutzflaeche): {} m2 ({}%)".format(
        metrics['HNF'], int(metrics['HNF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("- **NNF** (Nebennutzflaeche): {} m2 ({}%)".format(
        metrics['NNF'], int(metrics['NNF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("- **AGF** (Aussengeschossflaeche): {} m2 ({}%)".format(
        metrics['AGF'], int(metrics['AGF']/metrics['GF']*100) if metrics['GF'] > 0 else 0))
    output.print_md("")

    output.print_md("### Verhaeltnisse")
    output.print_md("- **FAW/GF** (Aussenwand/Geschossflaeche): {}".format(metrics['FAW/GF']))
    output.print_md("- **FB/GF** (Bedachung/Geschossflaeche): {}".format(metrics['FB/GF']))
    output.print_md("")

    # Schritt 4: Export
    output.print_md("---")
    output.print_md("## Export nach CSV/Excel")

    success = export_to_csv(metrics, room_data)

    if success:
        output.print_md("")
        output.print_md("---")
        output.print_md("### Hinweise:")
        output.print_md("")
        output.print_md("- **Grundstuecksflaechen** (GSF, UF, BUF) muessen manuell nachgetragen werden")
        output.print_md("- **Raumkategorisierung** basiert auf Raumnamen-Keywords")
        output.print_md("- **GGF** wurde aus den Raumflaechen geschaetzt")
        output.print_md("")
        output.print_md("*SIA 416 Kennzahlen v1.0*")


# Script ausfuehren
if __name__ == "__main__":
    main()