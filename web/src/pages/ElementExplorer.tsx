import { useEffect, useState } from "react";
import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { fetchElements, fetchProject } from "../services/api";
import type { ElementsPage, ElementSummary, Project } from "../types/api";

interface ElementExplorerProps {
  projectId: string | null;
  webSelection: string[];
  onWebSelectionChange: (uuids: string[]) => void;
}

export function ElementExplorer({ projectId, webSelection, onWebSelectionChange }: ElementExplorerProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [pageData, setPageData] = useState<ElementsPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<ElementSummary | null>(null);

  const [search, setSearch] = useState("");
  const [elementType, setElementType] = useState("");
  const [layerId, setLayerId] = useState("");
  const [drawingFile, setDrawingFile] = useState("");
  const [attributeId, setAttributeId] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!projectId) return;
    fetchProject(projectId).then(setProject).catch(() => setProject(null));
  }, [projectId]);

  useEffect(() => {
    if (!projectId) return;
    fetchElements(projectId, {
      page,
      search: search || undefined,
      element_type: elementType || undefined,
      layer_id: layerId ? Number(layerId) : undefined,
      drawing_file_number: drawingFile ? Number(drawingFile) : undefined,
      attribute_id: attributeId ? Number(attributeId) : undefined,
    })
      .then((data) => {
        setPageData(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [projectId, page, search, elementType, layerId, drawingFile, attributeId]);

  if (!projectId) {
    return (
      <div>
        <h1 className="page-title">Element-Explorer</h1>
        <Banner kind="info">Bitte zuerst ein Projekt in der Projektübersicht öffnen.</Banner>
      </div>
    );
  }

  const totalPages = pageData ? Math.max(1, Math.ceil(pageData.total / pageData.page_size)) : 1;
  const typeOptions = Object.keys(project?.element_statistics?.counts_by_type ?? {});

  function toggleSelection(uuid: string) {
    if (webSelection.includes(uuid)) {
      onWebSelectionChange(webSelection.filter((u) => u !== uuid));
    } else {
      onWebSelectionChange([...webSelection, uuid]);
    }
  }

  return (
    <div>
      <h1 className="page-title">Element-Explorer</h1>
      <p className="page-subtitle">
        Synchronisierte Elementzusammenfassungen. Zeilen anklicken für Details,
        Kontrollkästchen für die Webauswahl (KI-Kontext).
      </p>

      {error ? <Banner kind="error">{error}</Banner> : null}

      <Card>
        <div className="form-row">
          <input
            placeholder="Suche (Name, Typ, UUID)…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            style={{ minWidth: "220px" }}
          />
          <select value={elementType} onChange={(e) => { setElementType(e.target.value); setPage(1); }}>
            <option value="">Alle Elementtypen</option>
            {typeOptions.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          <input
            placeholder="Layer-ID"
            value={layerId}
            onChange={(e) => { setLayerId(e.target.value); setPage(1); }}
            style={{ width: "100px" }}
          />
          <select value={drawingFile} onChange={(e) => { setDrawingFile(e.target.value); setPage(1); }}>
            <option value="">Alle Teilbilder</option>
            {(project?.drawing_files ?? []).map((file) => (
              <option key={file.number} value={String(file.number)}>
                {file.number} {file.name}
              </option>
            ))}
          </select>
          <input
            placeholder="Attribut-ID"
            value={attributeId}
            onChange={(e) => { setAttributeId(e.target.value); setPage(1); }}
            style={{ width: "110px" }}
          />
        </div>

        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th></th>
                <th>Typ</th>
                <th>Name</th>
                <th>Layer</th>
                <th>Teilbild</th>
                <th>Element-UUID</th>
              </tr>
            </thead>
            <tbody>
              {(pageData?.elements ?? []).map((element) => (
                <tr
                  key={element.element_uuid}
                  className={`clickable ${detail?.element_uuid === element.element_uuid ? "selected" : ""}`}
                  onClick={() => setDetail(element)}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={webSelection.includes(element.element_uuid)}
                      onChange={() => toggleSelection(element.element_uuid)}
                    />
                  </td>
                  <td>{element.element_type}</td>
                  <td>{element.display_name || "–"}</td>
                  <td>{element.layer_name ?? element.layer_id ?? "–"}</td>
                  <td>{element.drawing_file_number ?? "–"}</td>
                  <td className="mono">{element.element_uuid}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="pagination">
          <button className="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Zurück
          </button>
          <span>
            Seite {page} von {totalPages} ({pageData?.total ?? 0} Elemente)
          </span>
          <button className="secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            Weiter
          </button>
        </div>
      </Card>

      {detail ? (
        <Card title={`Detail: ${detail.display_name || detail.element_type}`}>
          <div className="detail-list">
            <dt>Element-UUID</dt>
            <dd className="mono">{detail.element_uuid}</dd>
            <dt>Modell-UUID</dt>
            <dd className="mono">{detail.model_element_uuid || "–"}</dd>
            <dt>Typ / Untertyp</dt>
            <dd>{detail.element_type} {detail.element_subtype ? ` / ${detail.element_subtype}` : ""}</dd>
            <dt>Layer</dt>
            <dd>{detail.layer_name ?? "–"} ({detail.layer_id ?? "–"})</dd>
            <dt>Teilbild</dt>
            <dd>{detail.drawing_file_number ?? "–"}</dd>
            <dt>Geometrieart</dt>
            <dd>{detail.geometry_kind || "–"} {detail.is_3d ? "(3D)" : ""}</dd>
            <dt>Bounding Box</dt>
            <dd className="mono">
              {detail.bounding_box
                ? `min(${detail.bounding_box.min.x.toFixed(0)}, ${detail.bounding_box.min.y.toFixed(0)}, ${detail.bounding_box.min.z.toFixed(0)}) – ` +
                  `max(${detail.bounding_box.max.x.toFixed(0)}, ${detail.bounding_box.max.y.toFixed(0)}, ${detail.bounding_box.max.z.toFixed(0)}) mm`
                : "–"}
            </dd>
            <dt>Mittelpunkt</dt>
            <dd className="mono">
              {detail.center
                ? `(${detail.center.x.toFixed(0)}, ${detail.center.y.toFixed(0)}, ${detail.center.z.toFixed(0)}) mm`
                : "–"}
            </dd>
            <dt>Elternelement</dt>
            <dd className="mono">{detail.parent_uuid || "–"}</dd>
            <dt>Kindelemente</dt>
            <dd>{detail.child_uuids.length}</dd>
          </div>
          {detail.attributes.length > 0 ? (
            <>
              <h3>Attribute</h3>
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Wert</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.attributes.map((attribute) => (
                      <tr key={attribute.attribute_id}>
                        <td>{attribute.attribute_id}</td>
                        <td>{attribute.name || "–"}</td>
                        <td>{String(attribute.value ?? "–")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
