# -*- coding: utf-8 -*-
"""
BKP Export mit Vorschau-Dialog
Zeigt alle verfuegbaren Dokumente (Hauptmodell + Links) und deren Kategorien an.
Der User kann auswaehlen, welche Elemente exportiert werden sollen.
"""

__title__ = "eBKP-H\nExport"
__author__ = "TA.BA_DT_PROGR_Gruppe21"
__doc__ = "Öffnet einen Dialog zur Auswahl der zu exportierenden Elemente aus Hauptmodell und Links"

from pyrevit import revit, DB, forms, script
from pyrevit.forms import WPFWindow
import os
import csv
from datetime import datetime
from System.Collections.ObjectModel import ObservableCollection

# Output fuer Meldungen
output = script.get_output()
doc = revit.doc


# ========================================
# DATENKLASSEN Elementauswahl in Revit
# ========================================

class CategoryItem(object):
    """Repraesentiert ein Element mit Anzahl"""
    def __init__(self, name, count, category_id, doc_id):
        self.Name = name
        self.Count = count
        self.CategoryId = category_id
        self.DocId = doc_id
        self._is_selected = True

    @property
    def IsSelected(self):
        return self._is_selected

    @IsSelected.setter
    def IsSelected(self, value):
        self._is_selected = value


class DocumentItem(object):
    """Repraesentiert ein Dokument (Hauptmodell oder Link)"""
    def __init__(self, name, doc_obj, is_link=False):
        self.Name = name
        self.Document = doc_obj
        self.IsLink = is_link
        self.Icon = "🔗" if is_link else "📄"
        self.Categories = ObservableCollection[object]()
        self._is_selected = True
        self._element_count = 0

    @property
    def IsSelected(self):
        return self._is_selected

    @IsSelected.setter
    def IsSelected(self, value):
        self._is_selected = value
        # Alle Kategorien auch setzen
        for cat in self.Categories:
            cat.IsSelected = value

    @property
    def ElementCount(self):
        return self._element_count

    def add_category(self, name, count, category_id):
        cat = CategoryItem(name, count, category_id, id(self.Document) if self.Document else 0)
        self.Categories.Add(cat)
        self._element_count += count


# ========================================
# HILFSFUNKTIONEN
# ========================================

def get_element_id_value(element_id):
    """Holt den Integer-Wert einer ElementId (kompatibel mit allen Revit-Versionen)"""
    try:
        if hasattr(element_id, 'Value'):
            return element_id.Value
        elif hasattr(element_id, 'IntegerValue'):
            return element_id.IntegerValue
        else:
            return int(str(element_id))
    except:
        return 0


def get_categories_with_counts(doc_to_scan):
    """Zaehlt Elemente pro Kategorie in einem Dokument"""
    # Kategorien die fuer BKP relevant sind
    relevant_categories = {
        DB.BuiltInCategory.OST_Rooms: "Raeume",
        DB.BuiltInCategory.OST_Walls: "Waende",
        DB.BuiltInCategory.OST_Ceilings: "Decken",
        DB.BuiltInCategory.OST_Floors: "Boeden",
        DB.BuiltInCategory.OST_Doors: "Tueren",
        DB.BuiltInCategory.OST_Windows: "Fenster",
        DB.BuiltInCategory.OST_Furniture: "Moebel",
        DB.BuiltInCategory.OST_ElectricalFixtures: "Elektro - Geraete",
        DB.BuiltInCategory.OST_ElectricalEquipment: "Elektro - Ausruestung",
        DB.BuiltInCategory.OST_CableTray: "Kabeltrassen",
        DB.BuiltInCategory.OST_Conduit: "Leerrohre",
        DB.BuiltInCategory.OST_LightingFixtures: "Leuchten",
        DB.BuiltInCategory.OST_LightingDevices: "Lichtschalter",
        DB.BuiltInCategory.OST_DataDevices: "Daten-Geraete",
        DB.BuiltInCategory.OST_FireAlarmDevices: "Brandmelder",
        DB.BuiltInCategory.OST_CommunicationDevices: "Kommunikation",
        DB.BuiltInCategory.OST_SecurityDevices: "Sicherheit",
        DB.BuiltInCategory.OST_PlumbingFixtures: "Sanitaer",
        DB.BuiltInCategory.OST_MechanicalEquipment: "HVAC - Geraete",
        DB.BuiltInCategory.OST_DuctTerminal: "Luftauslasse",
        DB.BuiltInCategory.OST_Sprinklers: "Sprinkler",
        DB.BuiltInCategory.OST_PipeAccessory: "Rohr-Zubehoer",
        DB.BuiltInCategory.OST_PipeFitting: "Rohrformteile",
        DB.BuiltInCategory.OST_GenericModel: "Allgemeine Modelle",
    }

    results = []

    for bic, name in relevant_categories.items():
        try:
            collector = DB.FilteredElementCollector(doc_to_scan)\
                .OfCategory(bic)\
                .WhereElementIsNotElementType()

            count = collector.GetElementCount()
            if count > 0:
                results.append((name, count, bic))
        except:
            pass

    return results


def scan_all_documents():
    """Scannt Hauptdokument und alle Links"""
    documents = []

    # Hauptdokument
    main_doc_item = DocumentItem(doc.Title, doc, is_link=False)
    categories = get_categories_with_counts(doc)
    for name, count, cat_id in categories:
        main_doc_item.add_category(name, count, cat_id)
    documents.append(main_doc_item)

    # Revit Links
    link_instances = DB.FilteredElementCollector(doc)\
        .OfClass(DB.RevitLinkInstance)\
        .ToElements()

    for link in link_instances:
        try:
            link_doc = link.GetLinkDocument()
            if link_doc:
                link_item = DocumentItem(link_doc.Title, link_doc, is_link=True)
                categories = get_categories_with_counts(link_doc)
                for name, count, cat_id in categories:
                    link_item.add_category(name, count, cat_id)

                if link_item.ElementCount > 0:
                    documents.append(link_item)
        except Exception as e:
            output.print_md("**Warnung:** Link konnte nicht geladen werden: {}".format(str(e)))

    return documents


def get_parameter_value(element, param_name):
    """Holt Parameterwert als String"""
    try:
        param = element.LookupParameter(param_name)
        if param and param.HasValue:
            if param.StorageType == DB.StorageType.String:
                return param.AsString() or ""
            elif param.StorageType == DB.StorageType.Double:
                return str(round(param.AsDouble(), 3))
            elif param.StorageType == DB.StorageType.Integer:
                return str(param.AsInteger())
            elif param.StorageType == DB.StorageType.ElementId:
                return str(get_element_id_value(param.AsElementId()))
        return ""
    except:
        return ""


def round_length_mm(value_in_feet):
    """
    Konvertiert Laenge von Revit-Einheiten (feet) zu mm mit 0 Kommastellen.

    Args:
        value_in_feet: Laengenwert in Revit-Einheiten (feet)

    Returns:
        int: Laenge in mm, gerundet auf 0 Kommastellen
    """
    return int(round(value_in_feet * 304.8, 0))


def round_area_m2(value_in_sqft):
    """
    Konvertiert Flaeche von Revit-Einheiten (sqft) zu m2 mit 2 Kommastellen.

    Args:
        value_in_sqft: Flaechenwert in Revit-Einheiten (square feet)

    Returns:
        float: Flaeche in m2, gerundet auf 2 Kommastellen
    """
    return round(value_in_sqft * 0.092903, 2)


def round_volume_m3(value_in_cuft):
    """
    Konvertiert Volumen von Revit-Einheiten (cuft) zu m3 mit 3 Kommastellen.

    Args:
        value_in_cuft: Volumenwert in Revit-Einheiten (cubic feet)

    Returns:
        float: Volumen in m3, gerundet auf 3 Kommastellen
    """
    return round(value_in_cuft * 0.0283168, 3)


def get_compound_structure(element, target_doc):
    """
    Holt den strukturellen Aufbau eines Elements (Wand, Boden, Decke) mit allen Schichten.

    Returns:
        Tuple: (aufbau_string, gesamtdicke_mm)
        aufbau_string: z.B. "Gipskarton (12.5mm) | Daemmung (50mm) | Beton (200mm)"
    """
    try:
        # Element-Typ holen je nach Kategorie
        element_type = None
        if hasattr(element, 'WallType'):
            element_type = element.WallType
        elif hasattr(element, 'FloorType'):
            element_type = element.FloorType
        elif hasattr(element, 'GetTypeId'):
            type_id = element.GetTypeId()
            if type_id and type_id != DB.ElementId.InvalidElementId:
                element_type = target_doc.GetElement(type_id)

        if not element_type:
            return "", 0

        # CompoundStructure holen
        compound = None
        if hasattr(element_type, 'GetCompoundStructure'):
            compound = element_type.GetCompoundStructure()

        if not compound:
            # Keine Schichtstruktur - versuche Gesamtdicke zu holen
            width_param = element_type.LookupParameter("Breite") or element_type.LookupParameter("Width") \
                          or element_type.LookupParameter("Dicke") or element_type.LookupParameter("Thickness")
            if width_param and width_param.HasValue:
                width_mm = round_length_mm(width_param.AsDouble())  # ft -> mm
                return "Einschichtig", width_mm
            return "", 0

        layers = compound.GetLayers()
        layer_infos = []
        total_thickness = 0

        # Schichtfunktionen uebersetzen
        function_names = {
            DB.MaterialFunctionAssignment.Structure: "Tragend",
            DB.MaterialFunctionAssignment.Substrate: "Substrat",
            DB.MaterialFunctionAssignment.Insulation: "Daemmung",
            DB.MaterialFunctionAssignment.Finish1: "Finish 1",
            DB.MaterialFunctionAssignment.Finish2: "Finish 2",
            DB.MaterialFunctionAssignment.Membrane: "Membran",
            DB.MaterialFunctionAssignment.StructuralDeck: "Tragendedecke",
        }

        for layer in layers:
            # Schichtdicke in mm
            thickness_mm = round_length_mm(layer.Width)  # ft -> mm
            total_thickness += thickness_mm

            # Material Name
            material_name = "Unbekannt"
            if layer.MaterialId and layer.MaterialId != DB.ElementId.InvalidElementId:
                material = target_doc.GetElement(layer.MaterialId)
                if material:
                    material_name = material.Name

            # Schichtfunktion
            function = function_names.get(layer.Function, "")

            # Info zusammenbauen
            if function:
                layer_info = "{} [{}] ({} mm)".format(material_name, function, thickness_mm)
            else:
                layer_info = "{} ({} mm)".format(material_name, thickness_mm)

            layer_infos.append(layer_info)

        aufbau_string = " | ".join(layer_infos)
        return aufbau_string, total_thickness

    except Exception as e:
        return "Fehler: {}".format(str(e)), 0


def get_wall_metrics(wall):
    """
    Holt Volumen, Flaeche, Laenge und Dicke einer Wand.

    Args:
        wall: Revit Wall Element

    Returns:
        tuple: (volume_m3, area_m2, length_m, thickness_mm)
        - volume_m3 (float): Volumen in m3 mit 3 Kommastellen
        - area_m2 (float): Flaeche in m2 mit 2 Kommastellen
        - length_m (float): Laenge in m mit 2 Kommastellen
        - thickness_mm (int): Dicke in mm mit 0 Kommastellen
    """
    try:
        volume_m3 = 0
        area_m2 = 0
        length_m = 0
        thickness_mm = 0

        # 1. Volumen holen
        vol_param = wall.LookupParameter("Volumen") or wall.LookupParameter("Volume")
        if vol_param and vol_param.HasValue:
            volume_m3 = round_volume_m3(vol_param.AsDouble())

        # 2. Flaeche holen
        area_param = wall.LookupParameter("Flaeche") or wall.LookupParameter("Area")
        if area_param and area_param.HasValue:
            area_m2 = round_area_m2(area_param.AsDouble())

        # 3. Laenge holen
        length_param = wall.LookupParameter("Laenge") or wall.LookupParameter("Length")
        if length_param and length_param.HasValue:
            # Konvertiere von feet zu Meter mit 2 Kommastellen
            length_m = round(length_param.AsDouble() * 0.3048, 2)

        # 4. Dicke holen (aus WallType)
        wall_type = wall.WallType
        if wall_type:
            width_param = wall_type.LookupParameter("Breite") or wall_type.LookupParameter("Width")
            if width_param and width_param.HasValue:
                thickness_mm = round_length_mm(width_param.AsDouble())

        # Fallback: Wenn Volumen nicht verfuegbar, berechne aus Flaeche * Dicke
        if volume_m3 == 0 and area_m2 > 0 and thickness_mm > 0:
            volume_m3 = round(area_m2 * (thickness_mm / 1000.0), 3)

        return volume_m3, area_m2, length_m, thickness_mm

    except:
        return 0, 0, 0, 0


def export_elements(selected_docs, output_path):
    """Exportiert die ausgewaehlten Elemente"""
    all_data = []

    # Kategorien-Mapping (BuiltInCategory -> Name)
    category_names = {
        DB.BuiltInCategory.OST_Rooms: "Raeume",
        DB.BuiltInCategory.OST_Walls: "Waende",
        DB.BuiltInCategory.OST_Ceilings: "Decken",
        DB.BuiltInCategory.OST_Floors: "Boeden",
        DB.BuiltInCategory.OST_Doors: "Tueren",
        DB.BuiltInCategory.OST_Windows: "Fenster",
        DB.BuiltInCategory.OST_ElectricalFixtures: "Elektro",
        DB.BuiltInCategory.OST_ElectricalEquipment: "Elektro",
        DB.BuiltInCategory.OST_LightingFixtures: "Beleuchtung",
        DB.BuiltInCategory.OST_LightingDevices: "Beleuchtung",
        DB.BuiltInCategory.OST_DataDevices: "Daten",
        DB.BuiltInCategory.OST_FireAlarmDevices: "Sicherheit",
        DB.BuiltInCategory.OST_CommunicationDevices: "Kommunikation",
        DB.BuiltInCategory.OST_SecurityDevices: "Sicherheit",
        DB.BuiltInCategory.OST_PlumbingFixtures: "Sanitaer",
        DB.BuiltInCategory.OST_MechanicalEquipment: "HVAC",
        DB.BuiltInCategory.OST_DuctTerminal: "HVAC",
        DB.BuiltInCategory.OST_Sprinklers: "Brandschutz",
        DB.BuiltInCategory.OST_PipeAccessory: "Sanitaer",
        DB.BuiltInCategory.OST_PipeFitting: "Sanitaer",
        DB.BuiltInCategory.OST_GenericModel: "Allgemein",
        DB.BuiltInCategory.OST_Furniture: "Moebel",
        DB.BuiltInCategory.OST_CableTray: "Elektro",
        DB.BuiltInCategory.OST_Conduit: "Elektro",
    }

    for doc_item in selected_docs:
        if not doc_item.IsSelected:
            continue

        target_doc = doc_item.Document
        doc_name = doc_item.Name
        is_link = doc_item.IsLink

        for cat_item in doc_item.Categories:
            if not cat_item.IsSelected:
                continue

            try:
                elements = DB.FilteredElementCollector(target_doc)\
                    .OfCategory(cat_item.CategoryId)\
                    .WhereElementIsNotElementType()\
                    .ToElements()

                for elem in elements:
                    try:
                        # GUID (IFC kompatibel)
                        elem_guid = elem.UniqueId if hasattr(elem, 'UniqueId') else ""
                        elem_type = elem.Name if hasattr(elem, 'Name') else ""

                        # Familie
                        family_name = ""
                        if hasattr(elem, 'Symbol') and elem.Symbol:
                            if hasattr(elem.Symbol, 'Family') and elem.Symbol.Family:
                                family_name = elem.Symbol.Family.Name

                        # Kategorie
                        kategorie = category_names.get(cat_item.CategoryId, cat_item.Name)

                        # Ebene
                        level = ""
                        level_param = elem.LookupParameter("Ebene") or elem.LookupParameter("Level")
                        if level_param and level_param.HasValue:
                            level_id = level_param.AsElementId()
                            level_elem = target_doc.GetElement(level_id)
                            if level_elem:
                                level = level_elem.Name

                        # Zusatzinfo (verschiedene Parameter probieren)
                        zusatzinfo = ""
                        for param_name in ["Beschreibung", "Description", "Kommentar", "Comments", "Mark", "Marke"]:
                            value = get_parameter_value(elem, param_name)
                            if value:
                                zusatzinfo = value
                                break

                        # Menge und Einheit
                        menge = 1
                        einheit = "Stk"
                        schichtaufbau = ""
                        dicke_mm = 0
                        wall_area = 0  # Fuer Waende
                        wall_length = 0  # Fuer Waende

                        # Fuer Raeume: Flaeche
                        if cat_item.CategoryId == DB.BuiltInCategory.OST_Rooms:
                            area_param = elem.LookupParameter("Flaeche") or elem.LookupParameter("Area")
                            if area_param and area_param.HasValue:
                                menge = round_area_m2(area_param.AsDouble())
                                einheit = "m2"

                        # Fuer Waende: Volumen, Flaeche, Laenge und Schichtaufbau
                        elif cat_item.CategoryId == DB.BuiltInCategory.OST_Walls:
                            # Volumen, Flaeche, Laenge und Dicke holen
                            menge, wall_area, wall_length, dicke_mm = get_wall_metrics(elem)
                            einheit = "m3"

                            # Schichtaufbau holen (dicke_mm wird hier ueberschrieben falls verfuegbar)
                            schichtaufbau, compound_thickness = get_compound_structure(elem, target_doc)
                            if compound_thickness > 0:
                                dicke_mm = compound_thickness

                        # Fuer Decken: Flaeche und Schichtaufbau
                        elif cat_item.CategoryId == DB.BuiltInCategory.OST_Ceilings:
                            area_param = elem.LookupParameter("Flaeche") or elem.LookupParameter("Area")
                            if area_param and area_param.HasValue:
                                menge = round_area_m2(area_param.AsDouble())
                                einheit = "m2"

                            # Schichtaufbau holen
                            schichtaufbau, dicke_mm = get_compound_structure(elem, target_doc)

                        # Fuer Boeden: Flaeche und Schichtaufbau
                        elif cat_item.CategoryId == DB.BuiltInCategory.OST_Floors:
                            area_param = elem.LookupParameter("Flaeche") or elem.LookupParameter("Area")
                            if area_param and area_param.HasValue:
                                menge = round_area_m2(area_param.AsDouble())
                                einheit = "m2"

                            # Schichtaufbau holen
                            schichtaufbau, dicke_mm = get_compound_structure(elem, target_doc)

                        # Daten sammeln
                        row = {
                            'Quelle': doc_name,
                            'GUID': elem_guid,
                            'Ebene': level,
                            'Kategorie': kategorie,
                            'Familie': family_name,
                            'Typ': elem_type,
                            'Menge': menge,
                            'Einheit': einheit,
                            'Dicke_mm': dicke_mm if dicke_mm > 0 else "",
                            'Schichtaufbau': schichtaufbau,
                            'Zusatzinfo': zusatzinfo,
                            'Fläche_m2': wall_area if wall_area > 0 else "",
                            'Länge_m': wall_length if wall_length > 0 else ""
                        }
                        all_data.append(row)

                    except Exception as e:
                        pass  # Einzelne Elemente ueberspringen bei Fehler

            except Exception as e:
                output.print_md("**Fehler** bei Kategorie {}: {}".format(cat_item.Name, str(e)))

    # CSV schreiben
    if all_data:
        fieldnames = ['Quelle', 'GUID', 'Kategorie', 'Typ', 'Familie',
                      'Zusatzinfo', 'Menge', 'Einheit', 'Ebene', 'Schichtaufbau', 'Dicke_mm', 'Fläche_m2', 'Länge_m']

        with open(output_path, 'wb') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for row in all_data:
                # Encode fuer Python 2
                encoded_row = {}
                for k, v in row.items():
                    if isinstance(v, unicode):
                        encoded_row[k] = v.encode('utf-8')
                    else:
                        encoded_row[k] = v
                writer.writerow(encoded_row)

        return len(all_data)
    return 0


# ========================================
# WPF DIALOG
# ========================================

class ExportDialog(WPFWindow):
    """Dialog zur Elementauswahl"""

    def __init__(self, xaml_file, documents):
        WPFWindow.__init__(self, xaml_file)
        self.documents = documents
        self.result = False

        # TreeView mit Daten fuellen
        self.treeDocuments.ItemsSource = ObservableCollection[object](documents)

        # Alle Knoten expandieren
        self.Loaded += self.on_loaded

        # Initiale Zusammenfassung
        self.update_summary()

    def on_loaded(self, sender, args):
        """Expandiert alle TreeView Items nach dem Laden"""
        self.expand_all(self.treeDocuments)

    def expand_all(self, tree_view):
        """Expandiert alle Items im TreeView"""
        for item in tree_view.Items:
            container = tree_view.ItemContainerGenerator.ContainerFromItem(item)
            if container:
                container.IsExpanded = True

    def update_summary(self):
        """Aktualisiert die Zusammenfassung"""
        selected_docs = 0
        selected_cats = 0
        total_elements = 0

        for doc_item in self.documents:
            if doc_item.IsSelected:
                selected_docs += 1
                for cat in doc_item.Categories:
                    if cat.IsSelected:
                        selected_cats += 1
                        total_elements += cat.Count

        self.txtSelectedDocs.Text = str(selected_docs)
        self.txtSelectedCats.Text = str(selected_cats)
        self.txtTotalElements.Text = str(total_elements)

    def DocCheckbox_Click(self, sender, args):
        """Handler fuer Dokument-Checkbox"""
        # Aktualisiere alle Kind-Kategorien
        data_context = sender.DataContext
        if data_context:
            for cat in data_context.Categories:
                cat.IsSelected = data_context.IsSelected
        self.update_summary()
        # TreeView aktualisieren
        self.treeDocuments.Items.Refresh()

    def CategoryCheckbox_Click(self, sender, args):
        """Handler fuer Kategorie-Checkbox"""
        self.update_summary()

    def SelectAll_Click(self, sender, args):
        """Alle auswaehlen"""
        for doc_item in self.documents:
            doc_item.IsSelected = True
            for cat in doc_item.Categories:
                cat.IsSelected = True
        self.update_summary()
        self.treeDocuments.Items.Refresh()

    def SelectNone_Click(self, sender, args):
        """Keine auswaehlen"""
        for doc_item in self.documents:
            doc_item._is_selected = False
            for cat in doc_item.Categories:
                cat._is_selected = False
        self.update_summary()
        self.treeDocuments.Items.Refresh()

    def Export_Click(self, sender, args):
        """Export starten"""
        self.result = True
        self.Close()

    def Cancel_Click(self, sender, args):
        """Abbrechen"""
        self.result = False
        self.Close()


# ========================================
# HAUPTPROGRAMM welches von pyRevit ausgeführt wird
# ========================================

def main():
    output.print_md("# BKP Export mit Vorschau")
    output.print_md("---")

    # Dokumente scannen
    output.print_md("Scanne Dokumente und Links...")
    documents = scan_all_documents()

    if not documents:
        forms.alert("Keine Dokumente gefunden!", title="Fehler")
        return

    # Zusammenfassung ausgeben
    total_docs = len(documents)
    total_links = sum(1 for d in documents if d.IsLink)
    total_elements = sum(d.ElementCount for d in documents)

    output.print_md("**Gefunden:**")
    output.print_md("- {} Dokument(e) ({} Hauptmodell, {} Links)".format(
        total_docs, total_docs - total_links, total_links))
    output.print_md("- {} Elemente insgesamt".format(total_elements))
    output.print_md("---")

    # XAML Datei finden
    script_dir = os.path.dirname(__file__)
    xaml_file = os.path.join(script_dir, "eBKP-H_Export.xaml")

    if not os.path.exists(xaml_file):
        forms.alert("XAML Datei nicht gefunden:\n{}".format(xaml_file), title="Fehler")
        return

    # Dialog anzeigen
    dialog = ExportDialog(xaml_file, documents)
    dialog.ShowDialog()

    if not dialog.result:
        output.print_md("**Abgebrochen.**")
        return

    # Speicherort waehlen
    default_name = "eBKP-H_Export_{}.csv".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_path = forms.save_file(
        file_ext='csv',
        default_name=default_name,
        title="CSV speichern unter"
    )

    if not output_path:
        output.print_md("**Abgebrochen.**")
        return

    # Export durchfuehren
    output.print_md("Exportiere Elemente...")

    count = export_elements(documents, output_path)

    if count > 0:
        output.print_md("---")
        output.print_md("## Export erfolgreich!")
        output.print_md("**{} Elemente** exportiert nach:".format(count))
        output.print_md("`{}`".format(output_path))
    else:
        forms.alert("Keine Elemente zum Exportieren ausgewaehlt!", title="Hinweis")


# Script ausfuehren
if __name__ == "__main__":
    main()
