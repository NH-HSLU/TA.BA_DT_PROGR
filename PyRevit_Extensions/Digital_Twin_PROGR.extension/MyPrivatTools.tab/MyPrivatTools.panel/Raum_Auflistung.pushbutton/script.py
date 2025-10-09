# -*- coding: utf-8 -*-
__title__ = "Räume\nzu CSV"
__author__ = "Dein Name"
__doc__ = "Exportiert alle Räume mit Flächen in eine CSV-Datei"

from pyrevit import revit, DB, forms, script
import csv
import os
import codecs

# Logger für Debug-Ausgaben
output = script.get_output()
logger = script.get_logger()

# Aktuelles Dokument
doc = revit.doc

logger.info("Starte Raumexport...")

# Räume sammeln
rooms_collector = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_Rooms)\
    .WhereElementIsNotElementType()

rooms = list(rooms_collector)

logger.info("Gefundene Räume: {}".format(len(rooms)))

# Prüfen ob Räume vorhanden sind
if not rooms:
    forms.alert("Keine Räume im Projekt gefunden.", exitscript=True)

# Daten sammeln
room_data = []
for room in rooms:
    try:
        # Raumparameter auslesen
        room_number = room.Number if room.Number else ""
        room_name_param = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME)
        room_name = room_name_param.AsString() if room_name_param else ""
        
        # Fläche in Quadratmetern
        area_param = room.get_Parameter(DB.BuiltInParameter.ROOM_AREA)
        if area_param:
            # Von internen Einheiten (Quadratfuß) zu Quadratmetern konvertieren
            area_sqft = area_param.AsDouble()
            try:
                # Für Revit 2021+
                area_sqm = DB.UnitUtils.ConvertFromInternalUnits(
                    area_sqft, 
                    DB.UnitTypeId.SquareMeters
                )
            except:
                # Für ältere Revit-Versionen
                area_sqm = DB.UnitUtils.ConvertFromInternalUnits(
                    area_sqft, 
                    DB.DisplayUnitType.DUT_SQUARE_METERS
                )
        else:
            area_sqm = 0.0
        
        # Ebene
        level = doc.GetElement(room.LevelId)
        level_name = level.Name if level else "Keine Ebene"
        
        # Raumdaten zur Liste hinzufügen
        room_data.append({
            'Raumnummer': room_number,
            'Raumname': room_name,
            'Fläche (m²)': round(area_sqm, 2),
            'Ebene': level_name
        })
        
        logger.debug("Raum hinzugefügt: {} - {}".format(room_number, room_name))
        
    except Exception as e:
        logger.warning("Fehler bei Raum {}: {}".format(room.Id, str(e)))
        continue

logger.info("Gesammelte Raumdaten: {}".format(len(room_data)))

# Speicherort wählen mit Windows Forms
from System.Windows.Forms import SaveFileDialog, DialogResult

save_dialog = SaveFileDialog()
save_dialog.Title = "Raumliste speichern"
save_dialog.Filter = "CSV Dateien (*.csv)|*.csv"
save_dialog.FileName = "Raumliste.csv"

result = save_dialog.ShowDialog()
logger.info("Dialog Ergebnis: {}".format(result))

if result == DialogResult.OK:
    file_path = save_dialog.FileName
    logger.info("Speichere nach: {}".format(file_path))
    
    try:
        # CSV-Datei schreiben mit codecs für IronPython
        with codecs.open(file_path, 'w', 'utf-8-sig') as csvfile:
            fieldnames = ['Raumnummer', 'Raumname', 'Fläche (m²)', 'Ebene']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', lineterminator='\n')
            
            writer.writeheader()
            writer.writerows(room_data)
        
        logger.info("CSV-Datei erfolgreich geschrieben!")
        
        # Prüfe ob Datei existiert
        if os.path.exists(file_path):
            logger.info("Datei existiert: {}".format(file_path))
            file_size = os.path.getsize(file_path)
            logger.info("Dateigröße: {} Bytes".format(file_size))
            
            forms.alert(
                "CSV-Export erfolgreich!\n{} Räume exportiert nach:\n{}".format(
                    len(room_data), 
                    file_path
                ),
                title="Export abgeschlossen"
            )
            
            # Datei öffnen
            os.startfile(file_path)
        else:
            logger.error("Datei wurde nicht erstellt!")
            forms.alert("Fehler: Datei wurde nicht erstellt!", title="Fehler")
            
    except Exception as e:
        logger.error("Fehler beim Schreiben der CSV: {}".format(str(e)))
        forms.alert("Fehler beim Schreiben der CSV:\n{}".format(str(e)), title="Fehler")
        
else:
    logger.info("Export abgebrochen")
    forms.alert("Export abgebrochen.")
