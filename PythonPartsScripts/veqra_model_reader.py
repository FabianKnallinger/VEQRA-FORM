"""VEQRA FORM - Lesender Modellzugriff (Adapter-Schicht, Allplan-Importe erlaubt).

Alle Zugriffe erfolgen ueber die dokumentierte Allplan Python API; jede
Funktion nennt das offizielle Beispiel bzw. den Doku-Abschnitt als Quelle.

Dokumentierte Grenzen dieser Version:
- Es werden nur Elemente des aktuellen Dokuments gelesen
  (ElementsSelectService.SelectAllElements liest das uebergebene Dokument).
- Es wird niemals Bildschirm-OCR verwendet; ausschliesslich Modellzugriff.
"""

from __future__ import annotations

# Importe wie in den offiziellen Beispielen (z. B. ShowObjectInformation.py,
# DrawingFileDataInteractor.py, ProjectAttributeService.py)
import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseEle
import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter

try:
    from .veqra_protocol import MAX_ATTRIBUTES_PER_ELEMENT, MAX_ELEMENTS_PER_SCAN, utc_now_iso
except ImportError:
    from veqra_protocol import MAX_ATTRIBUTES_PER_ELEMENT, MAX_ELEMENTS_PER_SCAN, utc_now_iso


def get_allplan_version() -> str:
    """Allplan-Version wie im offiziellen Beispiel (AllplanVersion.Version())."""

    # AllplanSettings.AllplanVersion.Version() wie im offiziellen Beispiel
    # ToolsAndStartExamples (build_ele.Version.value = AllplanVersion.Version())
    return str(AllplanSettings.AllplanVersion.Version())


def get_project_path() -> str:
    """Projektpfad wie in offiziellen Beispielen (AllplanPaths.GetCurPrjPath())."""

    # AllplanSettings.AllplanPaths.GetCurPrjPath() wie in offiziellen Beispielen,
    # z. B. BasisExamples/TextureMapping.py
    return str(AllplanSettings.AllplanPaths.GetCurPrjPath())


def get_project_name() -> str:
    """Projektname aus dem letzten Bestandteil des Projektpfads."""

    path = get_project_path().replace("\\", "/").rstrip("/")
    return path.rsplit("/", 1)[-1] if path else "Unbenanntes Projekt"


def get_project_attributes(doc: AllplanEleAdapter.DocumentAdapter,
                           limit: int = 500) -> list[dict]:
    """Projektattribute wie im offiziellen Beispiel ServiceExamples/ProjectAttributeService.py.

    Rueckgabeformat der API: Liste von Tupeln (Attribut-ID, Wert); Namen ueber
    AttributeService.GetAttributeName(doc, id).
    """

    # ProjectAttributeService.GetAttributesFromCurrentProject() wie im
    # offiziellen Beispiel ServiceExamples/ProjectAttributeService.py
    try:
        attributes = AllplanBaseEle.ProjectAttributeService.GetAttributesFromCurrentProject()
    except Exception as error:
        print("VEQRA FORM: Projektattribute nicht lesbar:", error)
        return []

    result = []
    for attribute in list(attributes)[:limit]:
        try:
            attribute_id = int(attribute[0])
            value = attribute[1]
            # AttributeService.GetAttributeName wie im offiziellen Beispiel
            # ServiceExamples/ProjectAttributeService.py
            name = str(AllplanBaseEle.AttributeService.GetAttributeName(doc, attribute_id))
            if isinstance(value, bool) or isinstance(value, (int, float)):
                clean_value: float | bool | str = value
            else:
                clean_value = str(value)[:1000]
            result.append({
                "attribute_id": attribute_id,
                "name": name[:255],
                "value": clean_value,
            })
        except Exception:
            continue
    return result


def _drawing_file_name(number: int) -> str:
    """Teilbildname wie in den offiziellen Beispielen
    DrawingFileDataInteractor.py und PaletteExamples/BasicControls/RadioButtons.py
    (DocumentNameService.GetDocumentNameByFileNumber).
    """

    try:
        return str(AllplanEleAdapter.DocumentNameService.GetDocumentNameByFileNumber(
            int(number), False, False, ""))
    except Exception:
        return ""


def get_drawing_files() -> list[dict]:
    """Geladene Teilbilder wie im offiziellen Beispiel InteractorExamples/DrawingFileDataInteractor.py.

    GetFileState() liefert (Teilbildnummer, DrawingFileLoadState);
    Namen ueber DocumentNameService.GetDocumentNameByFileNumber.
    """

    # DrawingFileService().GetFileState() wie im offiziellen Beispiel
    # InteractorExamples/DrawingFileDataInteractor.py
    file_service = AllplanBaseEle.DrawingFileService()
    file_states = file_service.GetFileState()

    # DrawingFileService.GetActiveFileNumber() wie im offiziellen Beispiel
    # InteractorExamples/ExportImportInteractor.py
    active_number = int(AllplanBaseEle.DrawingFileService.GetActiveFileNumber())

    result = []
    for number, load_state in file_states:
        state_name = str(load_state)
        if int(number) == active_number:
            mapped = "active"
        elif "Active" in state_name:
            mapped = "active_background"
        elif "Passive" in state_name:
            mapped = "passive_background"
        else:
            mapped = "loaded"
        result.append({"number": int(number),
                       "name": _drawing_file_name(int(number))[:255],
                       "load_state": mapped})
    return result


def _layer_name(layer_id: int) -> str | None:
    """Layername wie im offiziellen Beispiel (LayerService.GetNameByID)."""

    try:
        # LayerService.GetNameByID gemaess offizieller API-Referenz
        # NemAll_Python_BaseElements.LayerService
        return str(AllplanBaseEle.LayerService.GetNameByID(layer_id))
    except Exception:
        return None


def _point_to_dict(point) -> dict:
    return {"x": float(point.X), "y": float(point.Y), "z": float(point.Z)}


def get_bounding_box(elements: AllplanEleAdapter.BaseElementAdapterList) -> dict | None:
    """Bounding Box wie in offiziellen Beispielen (GetMinMaxBox(elements))."""

    if not elements:
        return None
    # AllplanBaseEle.GetMinMaxBox(elements) wie im offiziellen Beispiel
    # ContentExamples/TableScalable.py
    min_max = AllplanBaseEle.GetMinMaxBox(elements)
    try:
        return {"min": _point_to_dict(min_max.Min), "max": _point_to_dict(min_max.Max)}
    except AttributeError:
        return None


def element_summary(element: AllplanEleAdapter.BaseElementAdapter,
                    doc: AllplanEleAdapter.DocumentAdapter,
                    with_attributes: bool = True,
                    with_relations: bool = True) -> dict:
    """Elementzusammenfassung nach dem offiziellen Beispiel
    ModelObjectExamples/General/ShowObjectInformation.py.
    """

    summary: dict = {
        # GetElementUUID / GetModelElementUUID / GetDisplayName /
        # GetElementAdapterType / GetDrawingfileNumber / Is3DElement wie im
        # offiziellen Beispiel ShowObjectInformation.py
        "element_uuid": str(element.GetElementUUID()),
        "model_element_uuid": str(element.GetModelElementUUID()),
        "element_type": str(element.GetElementAdapterType().GetTypeName()),
        "element_subtype": None,
        "display_name": str(element.GetDisplayName()),
        "drawing_file_number": int(element.GetDrawingfileNumber()),
        "is_3d": bool(element.Is3DElement()),
        "attributes": [],
        "child_uuids": [],
    }

    # GetCommonProperties wie im offiziellen Beispiel ShowObjectInformation.py;
    # CommonProperties.Layer gemaess offizieller API-Referenz
    try:
        common = element.GetCommonProperties()
        layer_id = int(common.Layer)
        summary["layer_id"] = layer_id
        summary["layer_name"] = _layer_name(layer_id)
        summary["format_properties"] = {
            "pen": int(common.Pen),
            "stroke": int(common.Stroke),
            "color": int(common.Color),
            "pen_by_layer": bool(common.PenByLayer),
            "stroke_by_layer": bool(common.StrokeByLayer),
            "color_by_layer": bool(common.ColorByLayer),
            "help_construction": bool(common.HelpConstruction),
        }
    except Exception:
        summary["layer_id"] = None
        summary["layer_name"] = None
        summary["format_properties"] = None

    if with_attributes:
        # element.GetAttributes(eAttibuteReadState.ReadAll) und
        # AttributeService.GetAttributeName wie im offiziellen Beispiel
        # ShowObjectInformation.py
        try:
            attributes = element.GetAttributes(AllplanBaseEle.eAttibuteReadState.ReadAll)
            for attribute in list(attributes)[:MAX_ATTRIBUTES_PER_ELEMENT]:
                attribute_id = int(attribute[0])
                value = attribute[1]
                summary["attributes"].append({
                    "attribute_id": attribute_id,
                    "name": str(AllplanBaseEle.AttributeService.GetAttributeName(
                        doc, attribute_id)),
                    "value": value if isinstance(value, (int, float, bool)) else str(value),
                })
        except Exception:
            pass

    # Geometrieart wie im offiziellen Beispiel ShowObjectInformation.py
    # (element.GetGeometry()); nur der Typname, keine 3D-Netze
    try:
        geometry = element.GetGeometry()
        summary["geometry_kind"] = type(geometry).__name__ if geometry is not None else None
    except Exception:
        summary["geometry_kind"] = None

    # Bounding Box und Mittelpunkt ueber GetMinMaxBox
    box = get_bounding_box(AllplanEleAdapter.BaseElementAdapterList([element]))
    summary["bounding_box"] = box
    if box:
        summary["center"] = {
            "x": (box["min"]["x"] + box["max"]["x"]) / 2.0,
            "y": (box["min"]["y"] + box["max"]["y"]) / 2.0,
            "z": (box["min"]["z"] + box["max"]["z"]) / 2.0,
        }
    else:
        summary["center"] = None

    if with_relations:
        # BaseElementAdapterParentElementService.GetParentElement und
        # BaseElementAdapterChildElementsService.GetChildModelElementsFromTree
        # wie im offiziellen Beispiel ShowObjectInformation.py
        try:
            parent = AllplanEleAdapter.BaseElementAdapterParentElementService.GetParentElement(
                element)
            parent_uuid = str(parent.GetElementUUID())
            summary["parent_uuid"] = (parent_uuid
                                      if parent_uuid != summary["element_uuid"] else None)
        except Exception:
            summary["parent_uuid"] = None
        try:
            children = (AllplanEleAdapter.BaseElementAdapterChildElementsService
                        .GetChildModelElementsFromTree(element))
            summary["child_uuids"] = [str(child.GetElementUUID())
                                      for child in list(children)[:1000]]
        except Exception:
            summary["child_uuids"] = []

    summary["is_modifiable"] = None  # Ein dokumentierter Sperrstatus-Abruf existiert nicht
    return summary


def select_all_elements(doc: AllplanEleAdapter.DocumentAdapter
                        ) -> AllplanEleAdapter.BaseElementAdapterList:
    """Alle Elemente des Dokuments wie in offiziellen Beispielen
    (z. B. InteractorExamples/GetObjectAttributesInteractor.py).
    """

    # ElementsSelectService.SelectAllElements(doc) wie im offiziellen Beispiel
    # InteractorExamples/GetObjectAttributesInteractor.py
    return AllplanBaseEle.ElementsSelectService.SelectAllElements(doc)


def project_scan(doc: AllplanEleAdapter.DocumentAdapter) -> dict:
    """Projektscan: kompakte Zusammenfassung des aktuellen Dokuments.

    Zaehlt Elemente nach Typ und Layer und ermittelt die Bounding Box des
    dokumentiert zugaenglichen Modells. Es werden keine 3D-Netze uebertragen.
    Schlaegt das Lesen fehl, wird eine leere Statistik mit Warnung geliefert,
    damit die Projektsynchronisierung trotzdem moeglich bleibt.
    """

    try:
        elements = select_all_elements(doc)
    except Exception as error:
        print("VEQRA FORM: SelectAllElements fehlgeschlagen:", error)
        return {
            "total_count": 0,
            "counts_by_type": {},
            "counts_by_layer": {},
            "model_bounding_box": None,
            "warnings": ["Die Elemente des Dokuments konnten nicht gelesen werden."],
        }

    counts_by_type: dict[str, int] = {}
    counts_by_layer: dict[str, int] = {}
    warnings: list[str] = []
    total = 0

    for element in elements:
        total += 1
        if total > MAX_ELEMENTS_PER_SCAN:
            warnings.append(
                f"Mehr als {MAX_ELEMENTS_PER_SCAN} Elemente; die Statistik wurde begrenzt.")
            break

        try:
            type_name = str(element.GetElementAdapterType().GetTypeName())
        except Exception:
            type_name = "Unbekannt"
            if "Nicht lesbare Elementtypen vorhanden." not in warnings:
                warnings.append("Nicht lesbare Elementtypen vorhanden.")
        counts_by_type[type_name] = counts_by_type.get(type_name, 0) + 1

        try:
            layer_id = int(element.GetCommonProperties().Layer)
            layer_key = _layer_name(layer_id) or str(layer_id)
        except Exception:
            layer_key = "unbekannt"
        counts_by_layer[layer_key] = counts_by_layer.get(layer_key, 0) + 1

    try:
        bounding_box = get_bounding_box(elements)
    except Exception as error:
        print("VEQRA FORM: GetMinMaxBox fehlgeschlagen:", error)
        bounding_box = None
        warnings.append("Die Bounding Box konnte nicht ermittelt werden.")

    return {
        "total_count": min(total, MAX_ELEMENTS_PER_SCAN),
        "counts_by_type": counts_by_type,
        "counts_by_layer": counts_by_layer,
        "model_bounding_box": bounding_box,
        "warnings": warnings,
    }


def summarize_elements(elements, doc, source_note: str = "") -> tuple[list[dict], list[str]]:
    """Erzeugt Elementzusammenfassungen mit Begrenzung (max. Scanumfang)."""

    summaries: list[dict] = []
    warnings: list[str] = []

    for index, element in enumerate(elements):
        if index >= MAX_ELEMENTS_PER_SCAN:
            warnings.append(
                f"Mehr als {MAX_ELEMENTS_PER_SCAN} Elemente; die Übertragung wurde begrenzt.")
            break
        try:
            summaries.append(element_summary(element, doc))
        except Exception:
            warnings.append(f"Ein Element konnte nicht gelesen werden ({source_note}).")

    return summaries, warnings


def read_timestamp() -> str:
    return utc_now_iso()
