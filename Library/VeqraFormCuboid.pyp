<?xml version="1.0" encoding="utf-8"?>
<!--
    VEQRA FORM - Quader erstellen

    Aufbau der PYP-Datei nach dem offiziellen Allplan 2025 Beispiel:
    PythonPartsExamples/Library/Examples/PythonParts/GeometryExamples/BasicSolids/Cuboid.pyp
    (Branch 2025) sowie dem offiziellen Allplan 2025 PythonPart SDK
    (StartPythonDebug.pyp: Skriptname relativ zum Skriptordner des Plugins).
-->
<Element>
    <Script>
        <Name>VeqraFormCuboid.py</Name>
        <Title>VEQRA FORM</Title>
        <Version>0.1.0</Version>
    </Script>

    <Page>
        <Name>VeqraFormPage</Name>
        <Text>VEQRA FORM</Text>

        <Parameter>
            <Name>SubtitleText</Name>
            <Text>Aus Anweisung wird Geometrie.</Text>
            <Value></Value>
            <ValueType>Text</ValueType>
        </Parameter>

        <Parameter>
            <Name>SeparatorTop</Name>
            <Text></Text>
            <Value></Value>
            <ValueType>Separator</ValueType>
        </Parameter>

        <Parameter>
            <Name>DimensionsExpander</Name>
            <Text>Abmessungen</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>CuboidLength</Name>
                <Text>Länge</Text>
                <Value>8000</Value>
                <MinValue>1</MinValue>
                <ValueType>Length</ValueType>
            </Parameter>
            <Parameter>
                <Name>CuboidWidth</Name>
                <Text>Breite</Text>
                <Value>1200</Value>
                <MinValue>1</MinValue>
                <ValueType>Length</ValueType>
            </Parameter>
            <Parameter>
                <Name>CuboidHeight</Name>
                <Text>Höhe</Text>
                <Value>4500</Value>
                <MinValue>1</MinValue>
                <ValueType>Length</ValueType>
            </Parameter>
            <Parameter>
                <Name>UnitInfoText</Name>
                <Text>Einheit: Millimeter (mm)</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
        </Parameter>

        <Parameter>
            <Name>PlacementExpander</Name>
            <Text>Platzierung</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>HintText1</Name>
                <Text>Einfügepunkt im Zeichenbereich anklicken.</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>HintText2</Name>
                <Text>Die Vorschau des Quaders folgt dem Fadenkreuz.</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>HintText3</Name>
                <Text>Mit ESC brechen Sie ohne Modelländerung ab.</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>HintText4</Name>
                <Text>Werte kleiner oder gleich 0 mm werden abgelehnt.</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
        </Parameter>

    </Page>
</Element>
