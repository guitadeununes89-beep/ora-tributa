"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Identity = {
  display_name: string;
  organization_name: string;
  role: string;
  permissions: string[];
};

type NavigationItem = {
  label: string;
  href?: string;
  icon: string;
  future?: boolean;
  nested?: boolean;
  group?: boolean;
  requiredPermissions?: string[];
};

const navigation: NavigationItem[] = [
  { label: "Dashboard", href: "/", icon: "▦" },
  { label: "Consulta Tributária", href: "/reforma-tributaria/consulta", icon: "◇" },
  { label: "Produtos e Serviços", href: "/produtos", icon: "▣" },
  { label: "Reforma Tributária", icon: "§", group: true },
  { label: "Classificação IBS/CBS", href: "/reforma-tributaria/classificacao", icon: "◈", nested: true },
  { label: "Cobertura Normativa", href: "/reforma-tributaria/cobertura", icon: "◎", nested: true },
  { label: "Consulta ZFM (piloto)", href: "/reforma-tributaria/consulta-zfm", icon: "⛭", nested: true },
  { label: "Consulta Medicamentos (piloto)", href: "/reforma-tributaria/consulta-medicamentos", icon: "✚", nested: true },
  { label: "Consulta em Lote (piloto)", href: "/reforma-tributaria/consulta-lote", icon: "▤", nested: true },
  { label: "Imposto Seletivo", icon: "IS", future: true, nested: true },
  { label: "Transição 2026–2033", icon: "↗", future: true, nested: true },
  { label: "Simulação", icon: "∑", future: true, nested: true },
  { label: "Auditoria", icon: "✓", future: true },
  { label: "Planejamento Tributário", icon: "⌁", future: true },
  { label: "Base Legal", icon: "≣", future: true },
  { label: "Empresas", href: "/empresas", icon: "▤" },
  { label: "Curadoria", href: "/curadoria", icon: "⌘", requiredPermissions: ["CURATE_RULE", "APPROVE_RULE", "PUBLISH_RULE"] },
  { label: "Usuários e Papéis", href: "/configuracoes/usuarios", icon: "♙", requiredPermissions: ["MANAGE_MEMBERSHIP"] },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: Readonly<{ children: ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [executablePercentage, setExecutablePercentage] = useState<string | null>(null);

  useEffect(() => {
    if (pathname === "/login") return;
    void apiFetch("/auth/me").then(async (response) => {
      if (response.ok) setIdentity((await response.json()) as Identity);
      else setIdentity(null);
    });
  }, [pathname]);

  useEffect(() => {
    void apiFetch("/taxonomy/ibs-cbs/coverage").then(async (response) => {
      if (!response.ok) return;
      const data = (await response.json()) as { metrics: { executable_percentage: string } };
      setExecutablePercentage(data.metrics.executable_percentage.replace(".", ","));
    });
  }, []);

  async function logout() {
    const response = await apiFetch("/auth/logout", { method: "POST" });
    if (response.ok) {
      setIdentity(null);
      router.push("/login");
    }
  }

  if (pathname === "/login") return <div className="login-surface">{children}</div>;

  const visibleNavigation = navigation.filter((item) => !item.requiredPermissions
    || item.requiredPermissions.some((permission) => identity?.permissions.includes(permission)));

  return (
    <div className={`app-shell ${menuOpen ? "menu-open" : ""} ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <header className="topbar">
        <Link href="/" className="brand" aria-label="Plataforma de Inteligência Tributária">
          <span className="brand-mark">OT</span>
          <span><strong>Ora <span>Tributa</span></strong><small>Inteligência Fiscal</small></span>
        </Link>
        <div className="topbar-actions">
          <div className="topbar-indicator"><small>Cobertura executável</small><strong>{executablePercentage ? `${executablePercentage}%` : "…"}</strong></div>
          {identity ? <div className="context-strip" aria-label="Contexto ativo">
            <span><small>Organização ativa</small><strong>{identity.organization_name}</strong></span>
            <span><small>Empresa</small><strong>Não selecionada</strong></span>
            <span><small>Estabelecimento</small><strong>Não selecionado</strong></span>
            <span><small>Usuário</small><strong>{identity.display_name}</strong></span>
            <span><small>Perfil</small><strong>{identity.role}</strong></span>
          </div> :
            <Link href="/login" className="topbar-login">Entrar</Link>}
          {identity && <button className="icon-button" type="button" onClick={() => void logout()} aria-label="Sair">↪</button>}
          <button className="menu-button" type="button" onClick={() => setMenuOpen((value) => !value)} aria-label="Alternar menu">☰</button>
        </div>
      </header>
      <aside className="sidebar" aria-label="Navegação principal">
        <button className="sidebar-collapse" type="button" onClick={() => setSidebarCollapsed((value) => !value)} aria-label={sidebarCollapsed ? "Expandir menu" : "Recolher menu"}>{sidebarCollapsed ? "›" : "‹"}</button>
        <nav>
          {visibleNavigation.map((item) => item.group ? (
            <span className="nav-group" key={item.label}>
              <span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>
            </span>
          ) : item.href ? (
            <Link className={`${isActive(pathname, item.href) ? "active" : ""} ${item.nested ? "nav-nested" : ""}`.trim()} href={item.href} key={item.label} onClick={() => setMenuOpen(false)}>
              <span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>
            </Link>
          ) : (
            <span className={`nav-future ${item.nested ? "nav-nested" : ""}`.trim()} key={item.label} title="Em desenvolvimento">
              <span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span><small className="future-badge">Em desenvolvimento</small>
            </span>
          ))}
        </nav>
      </aside>
      <div className="app-content">{children}</div>
      {menuOpen && <button className="menu-backdrop" type="button" aria-label="Fechar menu" onClick={() => setMenuOpen(false)} />}
    </div>
  );
}
