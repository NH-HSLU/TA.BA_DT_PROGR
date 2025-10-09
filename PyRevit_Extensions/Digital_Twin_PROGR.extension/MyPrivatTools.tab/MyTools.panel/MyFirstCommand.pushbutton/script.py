# -*- coding: utf-8 -*-
"""Elektro Komponenten nach Raum mit BKP Export
Dieses Script listet für jeden Raum alle elektrischen Komponenten auf und exportiert sie als CSV.
"""

__title__ = "Elektro\nnach Raum\nBKP Export"
__author__ = "Dein Name"

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room
from pyrevit import revit, forms, script
from collections import defaultdict
import os
import codecs  # Für IronPython UTF-8 Support
import csv

# .NET Import für List
import clr
clr.AddReference("System")
from System.Collections.Generic import List

# Aktuelles Dokument
doc = revit.doc

# Aktive Phase holen
active_phase = doc.ActiveView.get_Parameter(BuiltInParameter.VIEW_PHASE).AsElementId()
if not active_phase or active_phase == ElementId.InvalidElementId:
    phases = FilteredElementCollector(doc).OfClass(Phase).ToElements()
    if phases and len(phases) > 0:
        active_phase = phases[-1].Id
    else:
        forms.alert("Keine Phase gefunden!", exitscript=True)

def get_bkp_code(element):
    """Holt BKP Code aus dem Element"""
    try:
        bkp_param_names = [
            "BKP",
            "BKP Code",
            "BKP-Code",
            "eBKP",
            "eBKP-H",
            "Baukostenplan",
            "Assembly Code"
        ]
        
        for param_name in bkp_param_names:
            param = element.LookupParameter(param_name)
            if param and param.HasValue:
                value = param.AsString()
                if value:
                    return value
        
        assembly_param = element.get_Parameter(BuiltInParameter.UNIFORMAT_CODE)
        if assembly_param and assembly_param.HasValue:
            return assembly_param.AsString()
        
        return "235"
        
    except:
        return "235"

def get_bkp_description(bkp_code):
    """Gibt BKP Beschreibung zurück basierend auf Code"""
    bkp_dict = {
        "230": "Gebäudetechnik",
        "231": "Heizung",
        "232": "Lüftung",
        "233": "Klimaanlage",
        "234": "Sanitär",
        "235": "Elektroanlagen",
        "235.1": "Stromversorgung",
        "235.2": "Beleuchtung",
        "235.3": "Kommunikation",
        "235.4": "Sicherheit",
        "235.5": "Gebäudeautomation",
        "236": "Transport",
        "237": "Förderer",
        "239": "Weitere Gebäudetechnik"
    }
    
    if bkp_code in bkp_dict:
        return bkp_dict[bkp_code]
    
    main_code = bkp_code.split(".")[0] if "." in bkp_code else bkp_code
    if main_code in bkp_dict:
        return bkp_dict[main_code]
    
    return "Nicht klassifiziert"

def get_element_name(element):
    """Sicherer Weg, um den Elementnamen zu erhalten"""
    try:
        if hasattr(element, 'Name') and element.Name:
            return element.Name
        
        if isinstance(element, FamilyInstance):
            symbol = element.Symbol
            if symbol:
                symbol_name = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if symbol_name:
                    return symbol_name.AsString()
        
        type_id = element.GetTypeId()
        if type_id and type_id != ElementId.InvalidElementId:
            elem_type = doc.GetElement(type_id)
            if elem_type and hasattr(elem_type, 'Name'):
                return elem_type.Name
        
        return "Unbenannt"
    except:
        return "Unbenannt"

def get_room_from_element(element):
    """Gibt den Raum zurück, in dem sich das Element befindet"""
    try:
        if isinstance(element, FamilyInstance):
            if hasattr(element, 'Room'):
                room = element.Room[doc.GetElement(active_phase)]
                if room:
                    return room
        
        if element.Location:
            point = None
            
            if hasattr(element.Location, 'Point'):
                point = element.Location.Point
            elif hasattr(element.Location, 'Curve'):
                curve = element.Location.Curve
                point = curve.Evaluate(0.5, True)
            
            if point:
                collector = FilteredElementCollector(doc)\
                    .OfCategory(BuiltInCategory.OST_Rooms)\
                    .WhereElementIsNotElementType()
                
                for room in collector:
                    if room.IsPointInRoom(point):
                        return room
    except:
        pass
    
    return None

# Elektrische Kategorien definieren
electrical_categories = [
    BuiltInCategory.OST_ElectricalEquipment,
    BuiltInCategory.OST_ElectricalFixtures,
    BuiltInCategory.OST_LightingFixtures,
    BuiltInCategory.OST_DataDevices,
    BuiltInCategory.OST_FireAlarmDevices,
    BuiltInCategory.OST_NurseCallDevices,
    BuiltInCategory.OST_SecurityDevices,
    BuiltInCategory.OST_TelephoneDevices,
    BuiltInCategory.OST_CommunicationDevices,
]

# .NET List erstellen
category_list = List[BuiltInCategory]()
for cat in electrical_categories:
    category_list.Add(cat)

# Multi-Category Filter erstellen
cat_filter = ElementMulticategoryFilter(category_list)

# Alle elektrischen Elemente sammeln
all_electrical = FilteredElementCollector(doc)\
    .WherePasses(cat_filter)\
    .WhereElementIsNotElementType()\
    .ToElements()

print("Gefundene elektrische Elemente: {}".format(len(list(all_electrical))))

# Liste für CSV Export
csv_data = []

# Elemente den Räumen zuordnen
for element in all_electrical:
    try:
        room = get_room_from_element(element)
        
        # Raum Informationen
        if room:
            room_number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            room_name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
            room_number = room_number_param.AsString() if room_number_param else "Ohne Nummer"
            room_name = room_name_param.AsString() if room_name_param else "Ohne Name"
        else:
            room_number = "N/A"
            room_name = "Ohne Raum"
        
        # Element Informationen
        element_name = get_element_name(element)
        
        # Category Name
        category_name = "Unbekannte Kategorie"
        if element.Category:
            category_name = element.Category.Name
        
        # BKP Code und Beschreibung
        bkp_code = get_bkp_code(element)
        bkp_description = get_bkp_description(bkp_code)
        
        # Element ID
        elem_id = int(element.Id.Value)
        
        # Zur CSV-Daten Liste hinzufügen
        csv_data.append({
            'Element_ID': elem_id,
            'Raum_Nummer': room_number,
            'Raum_Name': room_name,
            'BKP_Code': bkp_code,
            'BKP_Beschreibung': bkp_description,
            'Kategorie': category_name,
            'Element_Name': element_name
        })
        
    except Exception as e:
        print("Fehler bei Element ID {}: {}".format(int(element.Id.Value), str(e)))
        continue

# CSV Export
if csv_data:
    # Pfad für CSV-Datei wählen
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    default_filename = "Elektro_BKP_Export.csv"
    csv_file_path = forms.save_file(
        file_ext='csv',
        default_name=default_filename,
        init_dir=desktop_path
    )
    
    if csv_file_path:
        try:
            # CSV schreiben mit codecs für IronPython UTF-8 Support
            with codecs.open(csv_file_path, 'w', encoding='utf-8-sig') as csvfile:
                fieldnames = ['Element_ID', 'Raum_Nummer', 'Raum_Name', 'BKP_Code', 
                             'BKP_Beschreibung', 'Kategorie', 'Element_Name']
                
                # Header schreiben
                csvfile.write(';'.join(fieldnames) + '\n')
                
                # Daten schreiben
                for row in csv_data:
                    row_values = [unicode(row[field]) for field in fieldnames]
                    csvfile.write(';'.join(row_values) + '\n')
            
            print("\n" + "="*80)
            print("CSV EXPORT ERFOLGREICH")
            print("="*80)
            print("Datei gespeichert: {}".format(csv_file_path))
            print("Anzahl Elemente: {}".format(len(csv_data)))
            
            # Zusammenfassung nach BKP
            bkp_summary = defaultdict(int)
            for item in csv_data:
                bkp_summary[item['BKP_Code']] += 1
            
            print("\nZusammenfassung nach BKP:")
            for bkp, count in sorted(bkp_summary.items()):
                desc = get_bkp_description(bkp)
                print("  {} - {}: {} Elemente".format(bkp, desc, count))
            
            # Öffne CSV Datei
            os.startfile(csv_file_path)
            
        except Exception as e:
            forms.alert("Fehler beim Speichern der CSV: {}".format(str(e)))
    else:
        print("Export abgebrochen.")
else:
    forms.alert("Keine Daten zum Exportieren gefunden!")
