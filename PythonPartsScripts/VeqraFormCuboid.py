"""VEQRA FORM - Erstellung eines Quaders als Standard-PythonPart.

Adapter-Schicht: Nur dieses Modul importiert Allplan-Module.

Der gesamte Ablauf folgt dem offiziellen Allplan 2025 Beispiel
"GeometryExamples/BasicSolids/Cuboid" aus dem Repository
NemetschekAllplan/PythonPartsExamples (Branch 2025):

- Die Palette wird vollstaendig aus der PYP-Datei erzeugt.
- create_element() liefert die Geometrie im lokalen Ursprung zurueck.
- Einfuegepunkt, Vorschau am Fadenkreuz, Abbrechen mit ESC und die
  Rueckgaengig-Funktion uebernimmt das dokumentierte PythonParts-Framework
  fuer Standard-PythonParts. Beim Start erfolgt keine Modellaenderung.
"""

# Importe wie im offiziellen Beispiel GeometryExamples/BasicSolids/Cuboid.py;
# NemAll_Python_Utility.ShowMessageBox wie in offiziellen Beispielen,
# z. B. PrecastExamples/MWSPlacement.py
import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter
import NemAll_Python_Utility as AllplanUtil
from BuildingElement import BuildingElement
from CreateElementResult import CreateElementResult
from TypeCollections.ModelEleList import ModelEleList

# Relativer Import eines Nachbarmoduls wie im offiziellen Allplan 2025
# PythonPart SDK (DownloadPythonPartsExamples.py: "from . import GithubUtil")
from . import constants


def check_allplan_version(_build_ele: BuildingElement,
                          _version:   str) -> bool:
    """Prueft die aktuelle Allplan-Version.

    Einstiegspunkt wie im offiziellen Beispiel
    GeometryExamples/BasicSolids/Cuboid.py.

    Args:
        _build_ele: BuildingElement mit den Palettenparametern
        _version:   aktuelle Allplan-Version

    Returns:
        True/False, ob die Version vom Skript unterstuetzt wird
    """

    # Das Plugin wird per install-config.yml erst ab Allplan 2025 installiert
    return True


def create_element(build_ele: BuildingElement,
                   _doc:      AllplanEleAdapter.DocumentAdapter) -> CreateElementResult:
    """Erzeugt den Quader aus den Palettenwerten (intern in Millimetern).

    Einstiegspunkt wie im offiziellen Beispiel
    GeometryExamples/BasicSolids/Cuboid.py. Das Framework zeigt das
    Ergebnis waehrend der Punkteingabe als Vorschau an und schreibt es
    erst nach der Bestaetigung des Einfuegepunkts in das Dokument.

    Args:
        build_ele: BuildingElement mit den Palettenparametern
        _doc:      Dokument der Allplan-Zeichnungsdateien

    Returns:
        Ergebnis der Elementerstellung
    """

    length = build_ele.CuboidLength.value
    width = build_ele.CuboidWidth.value
    height = build_ele.CuboidHeight.value

    # Zusaetzliche Absicherung zur Palettenpruefung (MinValue in der PYP-Datei):
    # Ungueltige Werte -> deutsche Fehlermeldung, kein Element erstellen
    if not constants.validate_dimensions(length, width, height):
        # ShowMessageBox wie in offiziellen Beispielen, z. B.
        # StructuralFramingExamples/StructuralColumnWithCylinderHoles.py
        AllplanUtil.ShowMessageBox(constants.MSG_INVALID_DIMENSION, AllplanUtil.MB_OK)

        # Leeres Ergebnis wie in offiziellen Beispielen (kein Element)
        return CreateElementResult()

    # CommonProperties wie im offiziellen Beispiel
    # GeometryExamples/BasicSolids/Cuboid.py
    common_properties = AllplanSettings.AllplanGlobalSettings.GetCurrentCommonProperties()

    # ModelEleList wie im offiziellen Beispiel GeometryExamples/BasicSolids/Cuboid.py
    model_elements = ModelEleList(common_properties)

    # Polyhedron3D.CreateCuboid(AxisPlacement3D, Laenge, Breite, Hoehe)
    # wie im offiziellen Beispiel GeometryExamples/BasicSolids/Cuboid.py
    cuboid = AllplanGeo.Polyhedron3D.CreateCuboid(
        AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D(),
                                   AllplanGeo.Vector3D(1000, 0, 0),
                                   AllplanGeo.Vector3D(0, 0, 1000)),
        length,
        width,
        height)

    # append_geometry_3d wie im offiziellen Beispiel
    # GeometryExamples/BasicSolids/Cuboid.py
    model_elements.append_geometry_3d(cuboid)

    # Rueckgabe wie im offiziellen Beispiel GeometryExamples/BasicSolids/Cuboid.py
    return CreateElementResult(model_elements)
