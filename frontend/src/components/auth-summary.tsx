"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Identity = {
  display_name: string;
  organization_name: string;
  role: string;
  permissions: string[];
};

export function AuthSummary() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  useEffect(() => {
    void apiFetch("/auth/me").then(async (response) => {
      if (response.ok) setIdentity((await response.json()) as Identity);
    });
  }, []);
  if (!identity) return <p className="curation-warning">Sessão necessária. <Link href="/login">Entrar</Link></p>;
  return (
    <aside className="identity-card" aria-label="Contexto de acesso">
      <strong>{identity.display_name}</strong>
      <span>{identity.organization_name}</span>
      <span className="status">{identity.role}</span>
      <small>Ações: {identity.permissions.join(", ")}</small>
    </aside>
  );
}

