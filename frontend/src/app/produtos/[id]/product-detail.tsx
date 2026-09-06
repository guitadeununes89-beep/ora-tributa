"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Version = { id: string; version: number; description: string; ncm: string | null;
  recorded_at: string; recorded_by: string; change_reason: string; snapshot_hash: string;
  attributes: { key: string; value: { value?: string }; is_synthetic: boolean }[] };
type Product = { id: string; internal_code: string; description: string; ncm: string | null;
  status: string; current_version: number; current: Version; history: Version[] };

export function ProductDetail({ productId }: { productId: string }) {
  const [product, setProduct] = useState<Product | null>(null); const [error, setError] = useState(false);
  async function load() { const response = await apiFetch(`/products/${productId}`);
    if (!response.ok) { setError(true); return; } setProduct((await response.json()) as Product); }
  useEffect(() => { void apiFetch(`/products/${productId}`).then(async (response) => {
    if (!response.ok) { setError(true); return; } setProduct((await response.json()) as Product);
  }); }, [productId]);
  async function update(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    const response = await apiFetch(`/products/${productId}`, { method: "PATCH", body: JSON.stringify({
      description: data.get("description"), ncm: data.get("ncm") || null,
      change_reason: data.get("change_reason"),
    }) }); if (!response.ok) { setError(true); return; } await load();
  }
  if (error) return <p role="alert" className="curation-warning">Produto não encontrado ou sem acesso.</p>;
  if (!product) return <p>Carregando produto…</p>;
  return <>
    <span className="eyebrow">Versão atual {product.current_version}</span>
    <h1>{product.internal_code}</h1><p className="lead">{product.description}</p>
    <Link href={`/reforma-tributaria/consulta?product_id=${product.id}`} className="curation-link">
      Executar análise tributária →</Link>
    <form className="inline-form" onSubmit={update}>
      <label>Descrição<input name="description" defaultValue={product.description} required /></label>
      <label>NCM opcional<input name="ncm" defaultValue={product.ncm ?? ""} pattern="[0-9]{8}" /></label>
      <label>Motivo da alteração<input name="change_reason" required /></label>
      <button type="submit">Criar nova versão</button>
    </form>
    <section><h2>Histórico imutável</h2><div className="timeline">
      {product.history.map((version) => <article key={version.id}>
        <h3>Versão {version.version}</h3><p>{version.description}</p>
        <p>NCM: {version.ncm ?? "não informado"}</p><p>{version.change_reason}</p>
        <small>{version.recorded_at} · ator {version.recorded_by}<br />SHA-256 {version.snapshot_hash}</small>
      </article>)}
    </div></section>
  </>;
}
