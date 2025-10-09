# -*- coding: utf-8 -*-
__title__ = "Volumen-\nAuswertung"
__author__ = "BIM Team"
__doc__ = "Exportiert Volumenauswertung nach Baustoffen, Geschossen und Stärken als CSV"

import os
import csv
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *

# Revit Dokument abrufen
doc = revit.doc
uidoc = revit.uidoc

# Prüfen ob Dokument vorhanden
if not doc:
    forms.alert('Kein aktives Revit-Dokument gefunden!', exitscript=True)

print("Starte Volumenauswertung...")

# WICHTIG: Volumenberechnung aktivieren
try:
    with revit.Transaction("Volumenberechnung aktivieren"):
        area_volume_settings = AreaVolumeSettings.GetAreaVolumeSettings(doc)
        if area_volume_settings:
            # Volumenberechnungen aktivieren
            area_volume_settings.ComputeVolumes = True
            print("Volumenberechnung wurde aktiviert")
        else:
            print("WARNUNG: AreaVolumeSettings nicht verfügbar")
except Exception as e:
    print("Fehler beim Aktivieren der Volumenberechnung: {}".format(str(e)))

# Dokument regenerieren um Volumen zu berechnen
try:
    doc.Regenerate()
    print("Dokument wurde regeneriert")
except Exception as e:
    print("Fehler bei Regeneration: {}".format(str(e)))

# Ausgabepfad definieren
output_path = forms.save_file(file_ext='csv', default_name='Volumenauswertung')
if not output_path:
    script.exit()

# Kategorien für die Auswertung
categories = [
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_Roofs,
    BuiltInCategory.OST_Ceilings,
    BuiltInCategory.OST_StructuralFoundation
]

# Daten sammeln
volume_data = []
processed_elements = 0
skipped_elements = 0

for cat in categories:
    collector = FilteredElementCollector(doc)\
        .OfCategory(cat)\
        .WhereElementIsNotElementType()
    
    elements = list(collector)
    cat_obj = Category.GetCategory(doc, cat)
    cat_name = cat_obj.Name if cat_obj else "Unbekannt"
    print("Kategorie {}: {} Elemente gefunden".format(cat_name, len(elements)))
    
    for element in elements:
        try:
            processed_elements += 1
            
            # Geschoss ermitteln
            level_id = element.LevelId
            level_name = "Ohne Geschoss"
            if level_id and level_id != ElementId.InvalidElementId:
                level = doc.GetElement(level_id)
                if level:
                    level_name = level.Name
            
            # Elementtyp und Eigenschaften ermitteln
            element_type_id = element.GetTypeId()
            element_type = doc.GetElement(element_type_id) if element_type_id != ElementId.InvalidElementId else None
            
            type_name_param = element_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME) if element_type else None
            element_type_name = type_name_param.AsString() if type_name_param else "Unbekannt"
            
            family_name = "Unbekannt"
            if element_type and hasattr(element_type, 'FamilyName'):
                family_name = element_type.FamilyName
            
            # Breite/Stärke ermitteln
            width = 0.0
            width_param = None
            
            # Verschiedene Parameter für Breite/Dicke prüfen
            param_types = [
                BuiltInParameter.WALL_ATTR_WIDTH_PARAM,
                BuiltInParameter.FLOOR_ATTR_THICKNESS_PARAM,
                BuiltInParameter.ROOF_ATTR_THICKNESS_PARAM,
                BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH
            ]
            
            for param_type in param_types:
                width_param = element.get_Parameter(param_type)
                if not width_param and element_type:
                    width_param = element_type.get_Parameter(param_type)
                if width_param and width_param.HasValue:
                    try:
                        width = width_param.AsDouble()
                        # Konvertierung in Zentimeter
                        width = width * 30.48  # Von Fuß zu cm
                        break
                    except:
                        continue
            
            # Kategoriename
            kategorie_name = element.Category.Name if element.Category else "Unbekannt"
            
            # Geometrie-Optionen für bessere Volumenberechnung
            options = Options()
            options.ComputeReferences = True
            options.DetailLevel = ViewDetailLevel.Fine
            options.IncludeNonVisibleObjects = False
            
            # Material IDs abrufen
            material_ids = element.GetMaterialIds(False)
            
            has_volume = False
            
            if material_ids and material_ids.Count > 0:
                # Für jeden Baustoff im Element
                for mat_id in material_ids:
                    material = doc.GetElement(mat_id)
                    if not material:
                        continue
                    
                    try:
                        # Materialvolumen abrufen
                        volume_internal = element.GetMaterialVolume(mat_id)
                        
                        if volume_internal <= 0.0000001:
                            continue
                        
                        # Volumen in Kubikmeter umrechnen (von Kubikfuß)
                        volume_m3 = volume_internal * 0.0283168466  # Kubikfuß zu Kubikmeter
                        
                        if volume_m3 < 0.0001:
                            continue
                        
                        has_volume = True
                        
                        # Materialname und -klasse
                        mat_name = material.Name
                        mat_class = "Nicht klassifiziert"
                        if hasattr(material, 'MaterialClass'):
                            mat_class = material.MaterialClass
                        
                        # Baustofftyp zuordnen
                        baustoff = "Sonstige"
                        mat_lower = mat_name.lower()
                        
                        if any(x in mat_lower for x in ['beton', 'concrete', 'stahlbeton']):
                            baustoff = "Beton"
                        elif any(x in mat_lower for x in ['ziegel', 'backstein', 'brick', 'mauerwerk']):
                            baustoff = "Backstein"
                        elif any(x in mat_lower for x in ['stahl', 'steel', 'metall']):
                            baustoff = "Stahl"
                        elif any(x in mat_lower for x in ['holz', 'wood', 'timber']):
                            baustoff = "Holz"
                        elif any(x in mat_lower for x in ['dämmung', 'insulation', 'dämm']):
                            baustoff = "Dämmung"
                        elif any(x in mat_lower for x in ['glas', 'glass']):
                            baustoff = "Glas"
                        elif any(x in mat_lower for x in ['gips', 'gypsum']):
                            baustoff = "Gips"
                        
                        # Daten zur Liste hinzufügen
                        volume_data.append({
                            'Element_ID': element.Id.IntegerValue,
                            'Kategorie': kategorie_name,
                            'Geschoss': level_name,
                            'Baustoff': baustoff,
                            'Material_Name': mat_name,
                            'Material_Klasse': mat_class,
                            'Staerke_cm': round(width, 2),
                            'Volumen_m3': round(volume_m3, 4),
                            'Typ': element_type_name,
                            'Familie': family_name
                        })
                    except Exception as e:
                        continue
            
            # Fallback: Geometrie-basierte Volumenberechnung
            if not has_volume:
                try:
                    geom_element = element.get_Geometry(options)
                    
                    if geom_element:
                        for geom_obj in geom_element:
                            solid = None
                            
                            if isinstance(geom_obj, Solid):
                                solid = geom_obj
                            elif isinstance(geom_obj, GeometryInstance):
                                geom_inst = geom_obj.GetInstanceGeometry()
                                if geom_inst:
                                    for inst_obj in geom_inst:
                                        if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                                            solid = inst_obj
                                            break
                            
                            if solid and solid.Volume > 0.0000001:
                                # Volumen in Kubikmeter umrechnen
                                volume_m3 = solid.Volume * 0.0283168466
                                
                                if volume_m3 >= 0.0001:
                                    # Material vom Element holen (falls vorhanden)
                                    mat_name = "Geometrie"
                                    baustoff = "Geometrie (ohne Material)"
                                    
                                    struct_mat_param = element.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
                                    if struct_mat_param and struct_mat_param.HasValue:
                                        mat_elem = doc.GetElement(struct_mat_param.AsElementId())
                                        if mat_elem:
                                            mat_name = mat_elem.Name
                                            mat_lower = mat_name.lower()
                                            
                                            if any(x in mat_lower for x in ['beton', 'concrete']):
                                                baustoff = "Beton"
                                            elif any(x in mat_lower for x in ['ziegel', 'backstein', 'brick']):
                                                baustoff = "Backstein"
                                            elif any(x in mat_lower for x in ['stahl', 'steel']):
                                                baustoff = "Stahl"
                                            elif any(x in mat_lower for x in ['holz', 'wood']):
                                                baustoff = "Holz"
                                            else:
                                                baustoff = "Sonstige"
                                    
                                    volume_data.append({
                                        'Element_ID': element.Id.IntegerValue,
                                        'Kategorie': kategorie_name,
                                        'Geschoss': level_name,
                                        'Baustoff': baustoff,
                                        'Material_Name': mat_name,
                                        'Material_Klasse': 'N/A',
                                        'Staerke_cm': round(width, 2),
                                        'Volumen_m3': round(volume_m3, 4),
                                        'Typ': element_type_name,
                                        'Familie': family_name
                                    })
                                    has_volume = True
                                    break
                except Exception as e:
                    pass
            
            if not has_volume:
                skipped_elements += 1
        
        except Exception as e:
            skipped_elements += 1
            continue

print("\n=== Auswertung abgeschlossen ===")
print("Verarbeitete Elemente: {}".format(processed_elements))
print("Übersprungene Elemente: {}".format(skipped_elements))
print("Gefundene Datensätze: {}".format(len(volume_data)))

# CSV exportieren
if volume_data:
    try:
        with open(output_path, 'w') as csvfile:
            fieldnames = [
                'Element_ID', 
                'Kategorie', 
                'Geschoss', 
                'Baustoff', 
                'Material_Name',
                'Material_Klasse',
                'Staerke_cm', 
                'Volumen_m3',
                'Typ',
                'Familie'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', lineterminator='\n')
            writer.writeheader()
            
            for row in volume_data:
                # Encode für Windows-Kompatibilität
                encoded_row = {}
                for key, value in row.items():
                    if isinstance(value, unicode):
                        encoded_row[key] = value.encode('utf-8')
                    elif isinstance(value, str):
                        encoded_row[key] = value.decode('utf-8').encode('utf-8')
                    else:
                        encoded_row[key] = value
                writer.writerow(encoded_row)
        
        forms.alert(
            'Export erfolgreich!\n\n{} Datensätze exportiert nach:\n{}'.format(
                len(volume_data), 
                output_path
            ),
            title='Volumenauswertung'
        )
        
        # CSV-Datei automatisch öffnen
        try:
            import subprocess
            subprocess.Popen(['notepad.exe', output_path])
        except:
            pass
        
    except Exception as e:
        forms.alert('Fehler beim Schreiben der CSV-Datei:\n{}'.format(str(e)), exitscript=True)
else:
    forms.alert(
        'Keine Daten gefunden!\n\n'
        'Mögliche Ursachen:\n'
        '- Keine Elemente mit Materialien im Projekt\n'
        '- Alle Materialvolumina sind 0\n'
        '- Elemente haben keine gültige Geometrie\n\n'
        'Verarbeitete Elemente: {}\n'
        'Übersprungene Elemente: {}\n\n'
        'Bitte prüfen Sie:\n'
        '1. Ob das Projekt Wände, Decken oder Böden enthält\n'
        '2. Ob die Elemente Materialien zugewiesen haben\n'
        '3. Ob die Geometrie der Elemente korrekt ist\n\n'
        'Material-IDs der übersprungenen Elemente: {}'.format(processed_elements, skipped_elements, material_ids),
        exitscript=True
    )
