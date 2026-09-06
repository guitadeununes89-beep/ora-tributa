"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function ProductForm() {
  const router = useRouter(); const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    const response = await apiFetch("/products", { method: "POST", body: JSON.stringify({
      internal_code: data.get("internal_code"), description: data.get("description"),
      gtin: data.get("gtin") || null, ncm: data.get("ncm") || null, cest: data.get("cest") || null,
      unit: data.get("unit"), status: "ACTIVE", attributes: [],
      change_reason: "Initial product registration",
    }) });
    if (!response.ok) { setError("Não foi possível cadastrar. Revise os campos e sua permissão."); return; }
    const product = (await response.json()) as { id: string }; router.push(`/produtos/${product.id}`);
  }
  return <form className="stack-form" onSubmit={submit}>
    <label>Código interno<input name="internal_code" required maxLength={100} /></label>
    <label>Descrição<textarea name="description" required maxLength={2000} /></label>
    <label>GTIN opcional<input name="gtin" inputMode="numeric" pattern="[0-9]{8,14}" /></label>
    <label>NCM opcional<input name="ncm" inputMode="numeric" pattern="[0-9]{8}" /></label>
    <label>CEST opcional<input name="cest" inputMode="numeric" pattern="[0-9]{7}" /></label>
    <label>Unidade<input name="unit" required maxLength={20} /></label>
    <button type="submit">Cadastrar e criar versão 1</button>
    {error && <p role="alert" className="curation-warning">{error}</p>}
  </form>;
}
