"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Product = { id: string; internal_code: string; description: string; ncm: string | null;
  unit: string; status: string; current_version: number };

export function ProductList() {
  const [items, setItems] = useState<Product[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState(false);
  async function load(q = "") {
    const response = await apiFetch(`/products${q ? `?q=${encodeURIComponent(q)}` : ""}`);
    if (!response.ok) { setError(true); return; }
    setItems((await response.json()) as Product[]); setError(false);
  }
  useEffect(() => { void apiFetch("/products").then(async (response) => {
    if (!response.ok) { setError(true); return; }
    setItems((await response.json()) as Product[]);
  }); }, []);
  function search(event: FormEvent) { event.preventDefault(); void load(query.trim()); }
  return <section>
    <form className="inline-form" onSubmit={search}>
      <label>Buscar produto<input value={query} onChange={(e) => setQuery(e.target.value)} /></label>
      <button type="submit">Buscar</button>
    </form>
    {error && <p role="alert" className="curation-warning">Produtos indisponíveis para esta sessão.</p>}
    <div className="product-grid">{items.map((item) => <article key={item.id} className="product-card">
      <span className={`status status-${item.status.toLowerCase()}`}>{item.status}</span>
      <h2>{item.internal_code}</h2><p>{item.description}</p>
      <small>NCM {item.ncm ?? "não informado"} · {item.unit} · versão {item.current_version}</small><br />
      <Link href={`/produtos/${item.id}`}>Abrir histórico e análise</Link>
    </article>)}</div>
  </section>;
}
