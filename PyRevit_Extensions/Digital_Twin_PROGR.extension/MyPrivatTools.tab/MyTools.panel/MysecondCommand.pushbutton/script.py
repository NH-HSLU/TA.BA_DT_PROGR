# -*- coding: utf-8 -*-
"""IFC Attributierung Prüfen
Prüft ob IFC-relevante Parameter bei ausgewählten Elementen vorhanden und ausgefüllt sind.
"""
__title__ = "Räume mit\nKomponenten"
__author__ = "Orlando Bassi"

from Autodesk.Revit.DB import *
from pyrevit import revit, DB, forms
from pyrevit import script

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# Output für die Anzeige
output = script.get_output()

# Räume sammeln
rooms_collector = FilteredElementCollector(doc) \
    .OfCategory(BuiltInCategory.OST_Rooms) \
    .WhereElementIsNotElementType()

rooms = list(rooms_collector)

# Kategorien für MEP und Möbel definieren
categories_to_check = [
    BuiltInCategory.OST_MechanicalEquipment,
    BuiltInCategory.OST_ElectricalEquipment,
    BuiltInCategory.OST_ElectricalFixtures,
    BuiltInCategory.OST_LightingFixtures,
    BuiltInCategory.OST_PlumbingFixtures,
    BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_DuctTerminal,
    BuiltInCategory.OST_AirTerminals,
    BuiltInCategory.OST_GenericModel
]

# Alle relevanten Elemente sammeln
all_elements = []
for cat in categories_to_check:
    collector = FilteredElementCollector(doc) \
        .OfCategory(cat) \
        .WhereElementIsNotElementType()
    all_elements.extend(list(collector))

# Phase für Raum-Abfrage
phase = doc.Phases[doc.Phases.Size - 1]

output.print_md("# Räume und ihre Komponenten")
output.print_md("---")

# Durch Räume iterieren
for room in rooms:
    if room.Area > 0:  # Nur platzierte Räume
        room_number = room.Number
        room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
        room_area = room.Area * 0.092903  # Umrechnung in m²
        
        # Komponenten in diesem Raum finden
        components_in_room = []
        for element in all_elements:
            try:
                # Raum des Elements ermitteln
                elem_room = element.Room[phase]
                
                if elem_room and elem_room.Id == room.Id:
                    elem_name = element.Name
                    elem_category = element.Category.Name
                    elem_id = element.Id.IntegerValue
                    components_in_room.append((elem_category, elem_name, elem_id))
            except:
                pass
        
        # Ausgabe
        if components_in_room:
            output.print_md("## {} - {}".format(room_number, room_name))
            output.print_md("**Fläche:** {:.2f} m²".format(room_area))
            output.print_md("**Anzahl Komponenten:** {}".format(len(components_in_room)))
            
            # Komponenten auflisten
            for comp_cat, comp_name, comp_id in components_in_room:
                output.print_md("- {} | {} | ID: {}".format(comp_cat, comp_name, comp_id))
            
            output.print_md("---")

output.print_md("**Fertig!** Insgesamt {} Räume analysiert.".format(len([r for r in rooms if r.Area > 0])))
