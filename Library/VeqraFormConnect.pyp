<?xml version="1.0" encoding="utf-8"?>
<!--
    VEQRA FORM - Verbindungswerkzeug (Interactor PythonPart)

    Aufbau nach den offiziellen Allplan 2025 Beispielen:
    - StartPythonDebug.pyp aus dem PythonPart SDK (<Interactor>True</Interactor>, Constants)
    - PaletteExamples/ButtonControls/Buttons.pyp
      (Button mit EventId, eingebettet in einen Row-Container)
    - SelectionExamples (Text-Parameter als Statusanzeige)
-->
<Element>
    <Script>
        <Name>VeqraFormConnect.py</Name>
        <Title>VEQRA FORM</Title>
        <Version>0.2.0</Version>
        <Interactor>True</Interactor>
    </Script>

    <Constants>
        <Constant>
            <Name>CHECK_CONNECTION</Name>
            <Value>1001</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>SYNC_PROJECT</Name>
            <Value>1002</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>READ_SELECTION</Name>
            <Value>1003</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>SYNC_SELECTION</Name>
            <Value>1004</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>CHECK_COMMAND</Name>
            <Value>1005</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>PREVIEW_COMMAND</Name>
            <Value>1006</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>EXECUTE_COMMAND</Name>
            <Value>1007</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>REJECT_COMMAND</Name>
            <Value>1008</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>OPEN_WEB</Name>
            <Value>1009</Value>
            <ValueType>Integer</ValueType>
        </Constant>
    </Constants>

    <Page>
        <Name>VeqraConnectPage</Name>
        <Text>VEQRA FORM</Text>

        <Parameter>
            <Name>SubtitleText</Name>
            <Text>Aus Anweisung wird Geometrie.</Text>
            <Value></Value>
            <ValueType>Text</ValueType>
        </Parameter>

        <Parameter>
            <Name>StatusText</Name>
            <Text>Meldung</Text>
            <Value>Bereit.</Value>
            <ValueType>Text</ValueType>
        </Parameter>

        <Parameter>
            <Name>ConnectionExpander</Name>
            <Text>Verbindung</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>ConnectionText</Name>
                <Text>Status Bridge-Dienst</Text>
                <Value>Unbekannt</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ConnectorIdText</Name>
                <Text>Connector-ID</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>LastContactText</Name>
                <Text>Letzter Kontakt</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>PairingToken</Name>
                <Text>Pairing-Token</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>CheckConnectionRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>CheckConnectionButton</Name>
                    <Text>Verbindung prüfen</Text>
                    <EventId>CHECK_CONNECTION</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
        </Parameter>

        <Parameter>
            <Name>ProjectExpander</Name>
            <Text>Projekt</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>ProjectNameText</Name>
                <Text>Projektname</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ProjectIdText</Name>
                <Text>Projektkennung</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>DrawingFilesText</Name>
                <Text>Aktive Teilbilder</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ElementCountText</Name>
                <Text>Synchronisierte Elemente</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>LastSyncText</Name>
                <Text>Letzte Synchronisierung</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>SyncProjectRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>SyncProjectButton</Name>
                    <Text>Projekt synchronisieren</Text>
                    <EventId>SYNC_PROJECT</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
        </Parameter>

        <Parameter>
            <Name>SelectionExpander</Name>
            <Text>Auswahl</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>SelectionCountText</Name>
                <Text>Ausgewählte Elemente</Text>
                <Value>0</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>SelectionTypesText</Name>
                <Text>Erkannte Typen</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ReadSelectionRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>ReadSelectionButton</Name>
                    <Text>Auswahl lesen</Text>
                    <EventId>READ_SELECTION</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>SyncSelectionRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>SyncSelectionButton</Name>
                    <Text>Auswahl synchronisieren</Text>
                    <EventId>SYNC_SELECTION</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
        </Parameter>

        <Parameter>
            <Name>CommandsExpander</Name>
            <Text>Aufträge</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>PendingCountText</Name>
                <Text>Ausstehende Aufträge</Text>
                <Value>0</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>NextCommandText</Name>
                <Text>Nächster Auftrag</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>CheckCommandRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>CheckCommandButton</Name>
                    <Text>Auftrag prüfen</Text>
                    <EventId>CHECK_COMMAND</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>PreviewCommandRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>PreviewCommandButton</Name>
                    <Text>Vorschau</Text>
                    <EventId>PREVIEW_COMMAND</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>ExecuteCommandRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>ExecuteCommandButton</Name>
                    <Text>Ausführen</Text>
                    <EventId>EXECUTE_COMMAND</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>RejectCommandRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>RejectCommandButton</Name>
                    <Text>Ablehnen</Text>
                    <EventId>REJECT_COMMAND</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
        </Parameter>

        <Parameter>
            <Name>WebExpander</Name>
            <Text>Weboberfläche</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>WebAddressText</Name>
                <Text>Lokale Webadresse</Text>
                <Value>http://127.0.0.1:8899</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>WebHintText</Name>
                <Text>Hinweis</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>OpenWebRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>OpenWebButton</Name>
                    <Text>Weboberfläche öffnen</Text>
                    <EventId>OPEN_WEB</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
        </Parameter>

    </Page>
</Element>
