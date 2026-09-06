"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Company = { id: string; legal_name: string; trade_name: string | null; tax_id: string; status: string };

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [message, setMessage] = useState("");
  async function load() {
    const response = await apiFetch("/companies");
    if (response.ok) setCompanies((await response.json()) as Company[]);
    else setMessage("Entre com uma conta autorizada para consultar empresas.");
  }
  useEffect(() => {
    void apiFetch("/companies").then(async (response) => {
      if (response.ok) setCompanies((await response.json()) as Company[]);
      else setMessage("Entre com uma conta autorizada para consultar empresas.");
    });
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await apiFetch("/companies", { method: "POST", body: JSON.stringify({
      legal_name: data.get("legal_name"), trade_name: data.get("trade_name") || null,
      tax_id: data.get("tax_id"),
    }) });
    setMessage(response.ok ? "Empresa cadastrada." : "Cadastro não autorizado ou inválido.");
    if (response.ok) { event.currentTarget.reset(); await load(); }
  }
  return (
    <main className="management-page">
      <Link href="/">← Início</Link><span className="eyebrow">Organização ativa</span>
      <h1>Empresas</h1>
      <form onSubmit={submit} className="inline-form">
        <label>Razão social<input name="legal_name" required /></label>
        <label>Nome fantasia<input name="trade_name" /></label>
        <label>CNPJ fictício<input name="tax_id" inputMode="numeric" pattern="[0-9]{14}" required /></label>
        <button type="submit">Cadastrar</button>
      </form>
      {message && <p role="status">{message}</p>}
      <div className="table-wrap"><table><thead><tr><th>Razão social</th><th>Nome</th><th>Identificador</th><th>Status</th></tr></thead>
        <tbody>{companies.map((company) => <tr key={company.id}><td>{company.legal_name}</td><td>{company.trade_name ?? "—"}</td><td>{company.tax_id}</td><td><span className="status">{company.status}</span></td></tr>)}</tbody></table></div>
    </main>
  );
}

