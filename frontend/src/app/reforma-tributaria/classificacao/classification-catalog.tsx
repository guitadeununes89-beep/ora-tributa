"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Source = {
  title: string;
  official_url: string;
  technical_document: string;
  publication_date: string;
  artifact_hash: string;
  consulted_at: string;
  imported_at: string;
  status: string;
};

type Classification = {
  code: string;
  cst: string;
  cst_description: string | null;
  name: string;
  description: string;
  valid_from: string | null;
  valid_to: string | null;
  updated_on: string | null;
  attributes: Record<string, unknown>;
  catalog_version: string;
  source: Source;
};

export function ClassificationCatalog() {
  const [query, setQuery] = useState("");
  const [cst, setCst] = useState("");
  const [items, setItems] = useState<Classification[]>([]);
  const [selected, setSelected] = useState<Classification | null>(null);
  const [error, setError] = useState(false);

  async function load(search = "", cstCode = "") {
    const params = new URLSearchParams();
    if (search) params.set("q", search);
    if (cstCode) params.set("cst", cstCode);
    try {
      const response = await apiFetch(`/taxonomy/ibs-cbs/classifications?${params}`);
      if (!response.ok) throw new Error("unavailable");
      const data = (await response.json()) as Classification[];
      setItems(data);
      setSelected(data[0] ?? null);
      setError(false);
    } catch {
      setError(true);
    }
  }

useEffect(() => {
    void apiFetch("/taxonomy/ibs-cbs/classifications")
      .then(async (response) => {
        if (!response.ok) throw new Error("unavailable");
        const data = (await response.json()) as Classification[];
        setItems(data);
        setSelected(data[0] ?? null);
        setError(false);
      })
      .catch(() => setError(true));
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    void load(query.trim(), cst.trim());
  }

  return (
    <section aria-label="Catálogo de classificação IBS e CBS">
      <form onSubmit={submit} className="catalog-search">
        <label>
          Buscar código ou descrição
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <label>
          CST (3 dígitos)
          <input inputMode="numeric" pattern="[0-9]{3}" value={cst}
            onChange={(event) => setCst(event.target.value)} />
        </label>
        <button type="submit">Consultar snapshot publicado</button>
      </form>
      {error && <p role="alert" className="curation-warning">
        Catálogo indisponível para esta sessão ou ainda sem snapshot publicado.
      </p>}
      {!error && items.length === 0 && <p>Nenhuma classificação publicada encontrada.</p>}
      <CatalogHistory />
      <div className="catalog-layout">
        <div className="catalog-results" aria-label="Resultados">
          {items.map((item) => (
            <button key={`${item.catalog_version}-${item.code}`} type="button"
              className="catalog-result" onClick={() => setSelected(item)}>
              <strong>{item.code}</strong> · CST {item.cst}<br />
              <span>{item.name}</span>
            </button>
          ))}
        </div>
        {selected && <article className="catalog-detail" aria-live="polite">
          <span className="eyebrow">Snapshot {selected.catalog_version}</span>
          <h2>{selected.code} — {selected.name}</h2>
          <p><strong>CST {selected.cst}:</strong> {selected.cst_description}</p>
          <p>{selected.description}</p>
          <dl>
            <dt>Início de vigência</dt><dd>{selected.valid_from ?? "Não informado na fonte"}</dd>
            <dt>Fim de vigência</dt><dd>{selected.valid_to ?? "Sem data informada"}</dd>
            <dt>Atualização</dt><dd>{selected.updated_on ?? "Não informada"}</dd>
          </dl>
          <aside className="source-card" aria-label="Proveniência">
            <h3>Proveniência</h3>
            <p>{selected.source.title}</p>
            <p>{selected.source.technical_document} · publicação {selected.source.publication_date}</p>
            <p>Status {selected.source.status} · importado em {selected.source.imported_at}</p>
            <p>Fonte consultada em {selected.source.consulted_at}</p>
            <a href={selected.source.official_url} target="_blank" rel="noreferrer">Abrir fonte oficial</a>
            <p><small>SHA-256: <code>{selected.source.artifact_hash}</code></small></p>
          </aside>
          <details>
            <summary>Indicadores e atributos oficiais</summary>
            <pre>{JSON.stringify(selected.attributes, null, 2)}</pre>
          </details>
        </article>}
      </div>
    </section>
  );
}

type CatalogVersion = {
  id: string;
  version: string;
  status: string;
  publication_date: string;
  cst_count: number;
  cclasstrib_count: number;
};

function CatalogHistory() {
  const [catalogs, setCatalogs] = useState<CatalogVersion[]>([]);
  const [previous, setPrevious] = useState("");
  const [current, setCurrent] = useState("");
  const [diff, setDiff] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    void apiFetch("/taxonomy/ibs-cbs/catalogs?status=PUBLISHED")
      .then(async (response) => {
        if (!response.ok) return;
        const data = (await response.json()) as CatalogVersion[];
        setCatalogs(data);
        setCurrent(data[0]?.id ?? "");
        setPrevious(data[1]?.id ?? "");
      });
  }, []);

  async function compare() {
    if (!previous || !current) return;
    const response = await apiFetch(`/taxonomy/ibs-cbs/catalogs/${previous}/diff/${current}`);
    if (response.ok) setDiff((await response.json()) as Record<string, unknown>);
  }

  return (
    <details className="catalog-history">
      <summary>Histórico e comparação de snapshots</summary>
      <div className="inline-form">
        <label>Versão anterior
          <select value={previous} onChange={(event) => setPrevious(event.target.value)}>
            <option value="">Selecione</option>
            {catalogs.map((catalog) => <option key={catalog.id} value={catalog.id}>
              {catalog.version} · {catalog.publication_date}
            </option>)}
          </select>
        </label>
        <label>Versão posterior
          <select value={current} onChange={(event) => setCurrent(event.target.value)}>
            <option value="">Selecione</option>
            {catalogs.map((catalog) => <option key={catalog.id} value={catalog.id}>
              {catalog.version} · {catalog.publication_date}
            </option>)}
          </select>
        </label>
        <button type="button" disabled={!previous || !current} onClick={() => void compare()}>
          Comparar versões
        </button>
      </div>
      {catalogs.length < 2 && <p>O histórico terá comparação quando houver dois snapshots publicados.</p>}
      {diff && <pre aria-label="Diff normativo estruturado">{JSON.stringify(diff, null, 2)}</pre>}
    </details>
  );
}