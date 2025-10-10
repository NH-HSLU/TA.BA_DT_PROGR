# -*- coding: utf-8 -*-
__title__ = "Decken\nVolumenauswertung"
__author__ = "Your Name"
__doc__ = """Exportiert Decken-Daten zu CSV
Erstellt automatisch einen Schedule und exportiert die Daten
- Geschoss (Level)
- Deckentyp
- Fläche (m²)
- Volumen (m³)
- Dicke (m)"""

import os
import csv
from pyrevit import forms, revit, script
from Autodesk.Revit.DB import *

# Revit Dokument
doc = revit.doc
uidoc = revit.uidoc

# Sammle alle Decken
collector = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Floors)\
    .WhereElementIsNotElementType()

floors = list(collector)

if not floors:
    forms.alert("Keine Decken im Projekt gefunden!", title="Keine Daten", exitscript=True)

# Daten direkt von den Floor-Elementen sammeln
floor_data = []

for floor in floors:
    try:
        # Level
        level_name = "Kein Level"
        level_elevation = -999999.0
        level_id = floor.LevelId
        if level_id and level_id != ElementId.InvalidElementId:
            level = doc.GetElement(level_id)
            if level:
                level_name = level.Name
                if hasattr(level, 'Elevation'):
                    level_elevation = level.Elevation
        
        # Floor Type Name
        floor_type = doc.GetElement(floor.GetTypeId())
        floor_type_name = "Unbekannt"
        if floor_type:
            type_name_param = floor_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            if type_name_param:
                floor_type_name = type_name_param.AsString()
            else:
                floor_type_name = floor_type.Name
        
        # Fläche (m²)
        area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
        area_m2 = 0.0
        if area_param and area_param.HasValue:
            area_sq_feet = area_param.AsDouble()
            area_m2 = UnitUtils.ConvertFromInternalUnits(area_sq_feet, UnitTypeId.SquareMeters)
        
        # Volumen (m³)
        volume_param = floor.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED)
        volume_m3 = 0.0
        if volume_param and volume_param.HasValue:
            volume_cubic_feet = volume_param.AsDouble()
            volume_m3 = UnitUtils.ConvertFromInternalUnits(volume_cubic_feet, UnitTypeId.CubicMeters)
        
        # Dicke berechnen (Volumen / Fläche)
        thickness_m = volume_m3 / area_m2 if area_m2 > 0 else 0.0
        
        # Kommentare/Mark für zusätzliche Info
        comments = ""
        comments_param = floor.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if comments_param and comments_param.HasValue:
            comments = comments_param.AsString()
        
        floor_data.append({
            'Level': level_name,
            'Level_Elevation': level_elevation,
            'Floor_Type': floor_type_name,
            'Thickness': "{:.3f}".format(thickness_m),
            'Area': "{:.2f}".format(area_m2),
            'Volume': "{:.2f}".format(volume_m3),
            'Comments': comments
        })
    
    except Exception as e:
        print("Fehler bei Decke ID {}: {}".format(floor.Id, str(e)))
        continue

if not floor_data:
    forms.alert(
        "Keine Deckendaten gefunden!\n\n"
        "Das Projekt enthält {} Decke(n), aber keine Daten konnten extrahiert werden.".format(len(floors)),
        title="Keine Daten",
        exitscript=True
    )

# Sortiere nach Level, dann nach Floor Type
floor_data.sort(key=lambda x: (x['Level_Elevation'], x['Floor_Type']))

# CSV Export Dialog
save_path = forms.save_file(
    file_ext='csv',
    default_name='Decken_Volumenauswertung',
    title='Save Floor Schedule CSV'
)

if save_path:
    try:
        # CSV Datei schreiben
        with open(save_path, 'wb') as csvfile:
            # UTF-8 BOM für Excel-Kompatibilität
            csvfile.write(b'\xef\xbb\xbf')
        
        with open(save_path, 'ab') as csvfile:
            fieldnames = ['Level', 'Floor_Type', 'Thickness', 'Area', 'Volume', 'Comments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            
            # Header schreiben
            writer.writeheader()
            
            # Daten schreiben
            for row in floor_data:
                writer.writerow(row)
        
        forms.alert(
            'Decken-Volumenauswertung erfolgreich exportiert!\n\n'
            'Anzahl Decken: {}\n'
            'Datei: {}'.format(len(floor_data), save_path),
            title='Export Erfolgreich'
        )
        
        # Optional: Datei öffnen
        if forms.alert('CSV Datei jetzt öffnen?', yes=True, no=True):
            os.startfile(save_path)
            
    except Exception as e:
        forms.alert(
            'Fehler beim Export:\n{}'.format(str(e)),
            title='Export Fehler'
        )
else:
    forms.alert('Export abgebrochen', exitscript=True)
