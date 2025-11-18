# -*- coding: utf-8 -*-
__title__ = "Wände\nVolumenauswertung"
__author__ = "Nicole Hitz"
__doc__ = """Export Wall Schedule data to CSV file
Click to export wall information including:
- Level (Geschoss)
- Height (m)
- Length (m)
- Volume (m³)
- Width (m)
- Structural Material"""

import os
import csv
from collections import defaultdict
from pyrevit import forms, revit, script
from Autodesk.Revit.DB import *

# Revit Dokument
doc = revit.doc
uidoc = revit.uidoc

# Funktion um Parameter-Wert zu holen
def get_parameter_value(element, param_name):
    """Holt den Parameter-Wert als String"""
    param = element.LookupParameter(param_name)
    if param and param.HasValue:
        if param.StorageType == StorageType.Double:
            return param.AsValueString()  # Mit Einheiten
        elif param.StorageType == StorageType.String:
            return param.AsString()
        elif param.StorageType == StorageType.Integer:
            return str(param.AsInteger())
        elif param.StorageType == StorageType.ElementId:
            elem_id = param.AsElementId()
            if elem_id and elem_id != ElementId.InvalidElementId:
                elem = doc.GetElement(elem_id)
                if elem:
                    return elem.Name
    return ""

# Funktion um BuiltInParameter-Wert zu holen
def get_builtin_parameter_value(element, builtin_param):
    """Holt den BuiltInParameter-Wert"""
    param = element.get_Parameter(builtin_param)
    if param and param.HasValue:
        if param.StorageType == StorageType.Double:
            return param.AsValueString()
        elif param.StorageType == StorageType.String:
            return param.AsString()
        elif param.StorageType == StorageType.Integer:
            return str(param.AsInteger())
        elif param.StorageType == StorageType.ElementId:
            elem_id = param.AsElementId()
            if elem_id and elem_id != ElementId.InvalidElementId:
                elem = doc.GetElement(elem_id)
                if elem:
                    return elem.Name
    return ""

# Funktion um tatsächliche Höhe zu berechnen (in Meter)
def get_actual_height_meters(wall):
    """Berechnet die tatsächliche Höhe des Bauteils in Metern"""
    try:
        bbox = wall.get_BoundingBox(None)
        if bbox:
            # Höhe in Fuß (internal units)
            height_feet = bbox.Max.Z - bbox.Min.Z
            # Konvertiere zu Metern
            height_meters = UnitUtils.ConvertFromInternalUnits(height_feet, UnitTypeId.Meters)
            return "{:.2f}".format(height_meters)
    except:
        pass
    return ""

# Funktion um Länge in Meter zu konvertieren
def get_length_meters(wall):
    """Holt die Länge der Wand in Metern"""
    param = wall.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
    if param and param.HasValue:
        # Wert in Fuß (internal units)
        length_feet = param.AsDouble()
        # Konvertiere zu Metern
        length_meters = UnitUtils.ConvertFromInternalUnits(length_feet, UnitTypeId.Meters)
        return "{:.2f}".format(length_meters)
    return ""

# Funktion um Volumen in Kubikmeter zu konvertieren
def get_volume_cubic_meters(wall):
    """Holt das Volumen der Wand in Kubikmetern"""
    param = wall.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED)
    if param and param.HasValue:
        # Wert in Kubikfuß (internal units)
        volume_cubic_feet = param.AsDouble()
        # Konvertiere zu Kubikmetern
        volume_cubic_meters = UnitUtils.ConvertFromInternalUnits(volume_cubic_feet, UnitTypeId.CubicMeters)
        return "{:.2f}".format(volume_cubic_meters)
    return ""

# Funktion um Breite in Meter zu konvertieren (KORRIGIERT: vom WallType)
def get_width_meters(wall):
    """Holt die Breite der Wand in Metern vom WallType"""
    try:
        # Hole WallType von der Wall-Instanz
        wall_type = doc.GetElement(wall.GetTypeId())
        if wall_type and isinstance(wall_type, WallType):
            # Width Property vom WallType (in internal units = Fuß)
            width_feet = wall_type.Width
            # Konvertiere zu Metern
            width_meters = UnitUtils.ConvertFromInternalUnits(width_feet, UnitTypeId.Meters)
            return "{:.3f}".format(width_meters)
    except:
        pass
    return ""

# Funktion um Geschoss (Level) zu ermitteln
def get_wall_level(wall):
    """Ermittelt das Base Constraint Level einer Wand"""
    param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
    if param and param.HasValue:
        level_id = param.AsElementId()
        if level_id and level_id != ElementId.InvalidElementId:
            level = doc.GetElement(level_id)
            if level:
                return level.Name
    return "Kein Level"

# Funktion um Level Elevation zu ermitteln (für Sortierung)
def get_level_elevation(wall):
    """Ermittelt die Elevation des Base Constraint Levels für Sortierung"""
    param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
    if param and param.HasValue:
        level_id = param.AsElementId()
        if level_id and level_id != ElementId.InvalidElementId:
            level = doc.GetElement(level_id)
            if level and hasattr(level, 'Elevation'):
                return level.Elevation
    return -999999.0  # Sehr niedrige Zahl für Wände ohne Level

# Funktion um Structural Material zu ermitteln
def get_structural_material(wall):
    """Ermittelt das Structural Material einer Wand"""
    wall_type = doc.GetElement(wall.GetTypeId())
    if wall_type:
        # Compound Structure prüfen
        compound_structure = wall_type.GetCompoundStructure()
        if compound_structure:
            layers = compound_structure.GetLayers()
            # Suche nach Structural Layer
            for i, layer in enumerate(layers):
                if compound_structure.GetLayerFunction(i) == MaterialFunctionAssignment.Structure:
                    material_id = layer.MaterialId
                    if material_id and material_id != ElementId.InvalidElementId:
                        material = doc.GetElement(material_id)
                        if material:
                            return material.Name
            # Falls kein Structural Layer, nimm ersten Layer
            if len(layers) > 0:
                material_id = layers[0].MaterialId
                if material_id and material_id != ElementId.InvalidElementId:
                    material = doc.GetElement(material_id)
                    if material:
                        return material.Name
        
        # Fallback: Material Parameter
        material_param = wall_type.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
        if material_param and material_param.HasValue:
            material_id = material_param.AsElementId()
            if material_id and material_id != ElementId.InvalidElementId:
                material = doc.GetElement(material_id)
                if material:
                    return material.Name
    
    return ""

# Sammle alle Wände
collector = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Walls)\
    .WhereElementIsNotElementType()

walls = list(collector)

if not walls:
    forms.alert("Keine Wände im Projekt gefunden!", exitscript=True)

# Daten sammeln
wall_data = []

for wall in walls:
    # Level (Geschoss)
    level_name = get_wall_level(wall)
    level_elevation = get_level_elevation(wall)
    
    # Height (in Meter)
    height = get_actual_height_meters(wall)
    
    # Length (in Meter)
    length = get_length_meters(wall)
    
    # Volume (in Kubikmeter)
    volume = get_volume_cubic_meters(wall)
    
    # Width (in Meter) - KORRIGIERT: vom WallType
    width = get_width_meters(wall)
    
    # Structural Material
    structural_material = get_structural_material(wall)
    
    wall_data.append({
        'Level': level_name,
        'Level_Elevation': level_elevation,  # Für Sortierung
        'Height': height,
        'Length': length,
        'Volume': volume,
        'Width': width,
        'Structural Material': structural_material
    })

# Sortiere nach Level Elevation (Geschoss), dann nach Structural Material, dann nach Height
wall_data.sort(key=lambda x: (x['Level_Elevation'], x['Structural Material'], x['Height']))

# CSV Export Dialog
save_path = forms.save_file(
    file_ext='csv',
    default_name='Wall_Schedule',
    title='Save Wall Schedule CSV'
)

if save_path:
    try:
        # CSV Datei schreiben
        with open(save_path, 'wb') as csvfile:
            # UTF-8 BOM für Excel-Kompatibilität
            csvfile.write(b'\xef\xbb\xbf')
        
        with open(save_path, 'ab') as csvfile:
            # Level_Elevation nicht in CSV ausgeben (nur für Sortierung)
            fieldnames = ['Level', 'Height', 'Length', 'Volume', 'Width', 'Structural Material']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            
            # Header schreiben
            writer.writeheader()
            
            # Daten schreiben
            for row in wall_data:
                writer.writerow(row)
        
        forms.alert(
            'Wall Schedule erfolgreich exportiert!\n\n'
            'Anzahl Wände: {}\n'
            'Datei: {}'.format(len(wall_data), save_path),
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
