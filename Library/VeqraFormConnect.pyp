<?xml version="1.0" encoding="utf-8"?>
<!--
    VEQRA FORM - Verbindungswerkzeug (Interactor PythonPart)

    Aufbau nach den offiziellen Allplan 2025 Beispielen:
    - StartPythonDebug.pyp aus dem PythonPart SDK (<Interactor>True</Interactor>, Constants)
    - PaletteExamples/ButtonControls/Buttons.pyp (Button in Row-Container mit EventId)
    - PaletteExamples/BasicControls/EditControls.pyp (String = editierbares Eingabefeld)
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
        <Constant>
            <Name>SEND_AI</Name>
            <Value>1010</Value>
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
            <FontStyle>2</FontStyle>
        </Parameter>

        <Parameter>
            <Name>StatusText</Name>
            <Text>Status</Text>
            <Value>Bereit.</Value>
            <ValueType>Text</ValueType>
            <FontStyle>1</FontStyle>
        </Parameter>

        <Parameter>
            <Name>SeparatorStatus</Name>
            <Text></Text>
            <Value></Value>
            <ValueType>Separator</ValueType>
        </Parameter>

        <Parameter>
            <Name>AiExpander</Name>
            <Text>KI-Assistent</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>AiInfoText</Name>
                <Text>Anweisung eingeben und „An KI senden“ wählen.</Text>
                <Value></Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>AiContext</Name>
                <Text>Bereich</Text>
                <Value>0</Value>
                <ValueType>RadioButtonGroup</ValueType>

                <Parameter>
                    <Name>AiContextProject</Name>
                    <Text>Projekt</Text>
                    <Value>0</Value>
                    <ValueType>RadioButton</ValueType>
                </Parameter>
                <Parameter>
                    <Name>AiContextSelection</Name>
                    <Text>Auswahl</Text>
                    <Value>1</Value>
                    <ValueType>RadioButton</ValueType>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>AiPrompt</Name>
                <Text>Anweisung</Text>
                <Value></Value>
                <ValueType>String</ValueType>
            </Parameter>
            <Parameter>
                <Name>SendAiRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>SendAiButton</Name>
                    <Text>An KI senden</Text>
                    <EventId>SEND_AI</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>AiReplyText</Name>
                <Text>Antwort</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
        </Parameter>

        <Parameter>
            <Name>ConnectionExpander</Name>
            <Text>Verbindung</Text>
            <ValueType>Expander</ValueType>

            <Parameter>
                <Name>ConnectionText</Name>
                <Text>Bridge</Text>
                <Value>Unbekannt</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ConnectorIdText</Name>
                <Text>Connector</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>LastContactText</Name>
                <Text>Kontakt</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>PairingToken</Name>
                <Text>Token</Text>
                <Value></Value>
                <ValueType>String</ValueType>
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
                <Text>Name</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ProjectIdText</Name>
                <Text>Kennung</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>DrawingFilesText</Name>
                <Text>Teilbilder</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>ElementCountText</Name>
                <Text>Elemente</Text>
                <Value>–</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>LastSyncText</Name>
                <Text>Letzte Sync.</Text>
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
                <Text>Anzahl</Text>
                <Value>0</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>SelectionTypesText</Name>
                <Text>Typen</Text>
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
                <Text>Offen</Text>
                <Value>0</Value>
                <ValueType>Text</ValueType>
            </Parameter>
            <Parameter>
                <Name>NextCommandText</Name>
                <Text>Nächster</Text>
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
                <Name>PreviewExecuteRow</Name>
                <Text> </Text>
                <ValueType>Row</ValueType>
                <Parameter>
                    <Name>PreviewCommandButton</Name>
                    <Text>Vorschau</Text>
                    <EventId>PREVIEW_COMMAND</EventId>
                    <ValueType>Button</ValueType>
                </Parameter>
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
                <Text>Adresse</Text>
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
