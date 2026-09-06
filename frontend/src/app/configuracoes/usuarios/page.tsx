"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

const roles = ["VIEWER", "ANALYST", "CURATOR", "APPROVER", "PUBLISHER", "ADMIN"];
type Membership = { id: string; display_name: string; email: string; role: string; status: string };

export default function UsersPage() {
  const [items, setItems] = useState<Membership[]>([]);
  const [error, setError] = useState("");
  async function load() {
    const response = await apiFetch("/memberships");
    if (response.ok) setItems((await response.json()) as Membership[]);
    else setError("Apenas administradores da organização podem gerenciar acessos.");
  }
  useEffect(() => {
    void apiFetch("/memberships").then(async (response) => {
      if (response.ok) setItems((await response.json()) as Membership[]);
      else setError("Apenas administradores da organização podem gerenciar acessos.");
    });
  }, []);
  async function update(id: string, role: string) {
    const response = await apiFetch(`/memberships/${id}`, { method: "PATCH", body: JSON.stringify({ role }) });
    if (response.ok) await load(); else setError("Alteração não autorizada.");
  }
  return (
    <main className="management-page">
      <Link href="/">← Início</Link><span className="eyebrow">Configurações</span>
      <h1>Usuários e papéis</h1>
      <p className="lead">Papéis são explícitos e não formam uma hierarquia implícita.</p>
      {error && <p className="curation-warning" role="alert">{error}</p>}
      <div className="table-wrap"><table><thead><tr><th>Usuário</th><th>E-mail</th><th>Papel</th><th>Status</th></tr></thead>
        <tbody>{items.map((item) => <tr key={item.id}><td>{item.display_name}</td><td>{item.email}</td><td>
          <select aria-label={`Papel de ${item.display_name}`} value={item.role} onChange={(event) => void update(item.id, event.target.value)}>{roles.map((role) => <option key={role}>{role}</option>)}</select>
        </td><td>{item.status}</td></tr>)}</tbody></table></div>
    </main>
  );
}

