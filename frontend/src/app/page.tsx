import Link from "next/link";

const modules = [
  ["◇", "Consulta tributária", "/reforma-tributaria/consulta", "Inicie uma análise determinística com fatos, incertezas e evidências visíveis.", "Analisar"],
  ["◎", "Cobertura normativa", "/reforma-tributaria/cobertura", "Acompanhe os 164 cClassTrib por família e estágio de governança.", "Monitorar"],
  ["▣", "Produtos e serviços", "/produtos", "Administre cadastros versionados sem transformar descrição em regra.", "Gerenciar"],
  ["§", "Reforma Tributária", "/reforma-tributaria/classificacao", "Consulte o catálogo oficial de CST IBS/CBS e cClassTrib.", "Explorar"],
  ["▤", "Empresas", "/empresas", "Organizações, empresas e estabelecimentos no contexto autorizado.", "Configurar"],
  ["⌘", "Curadoria", "/curadoria", "Fontes, especificações, aprovações e publicação governada.", "Governar"],
] as const;
const future = ["Auditoria fiscal", "Planejamento tributário", "Base legal e relatórios"];

export default function Home() {
  return <main className="dashboard-home">
    <header className="dashboard-header"><div><h1>Dashboard</h1>
      <p className="lead">Visão nacional da Plataforma de Inteligência Tributária.</p></div>
      <Link href="/reforma-tributaria/cobertura" className="primary-link">Ver cobertura nacional →</Link></header>
    <section className="kpi-grid" role="status">
      <article className="kpi-card"><span>Catálogo oficial</span><strong>164</strong><small>cClassTrib publicadas</small></article>
      <article className="kpi-card green"><span>Fundamentos identificados</span><strong>163 de 164</strong><small>códigos com dispositivo estruturado</small></article>
      <article className="kpi-card orange"><span>Regra real publicada</span><strong>1 regra publicada</strong><small>Detalhe técnico: RT-IBSCBS-0003 · ruleset piloto</small></article>
      <article className="kpi-card red"><span>Cobertura executável</span><strong>0,61%</strong><small>1 de 164 cClassTrib</small></article><span hidden>O ruleset piloto não é default de produção.</span>
    </section>
    <section className="dashboard-toolbar"><strong>Escopo atual</strong><span>A única regra publicada pertence ao ruleset piloto explícito e não é default de produção.</span></section>
    <section className="module-panel"><header><div><span className="eyebrow">Atalhos executivos</span><h2>Áreas operacionais</h2></div><small>4 áreas prioritárias · 2 áreas de gestão</small></header>
      <div className="module-grid" aria-label="Áreas da plataforma">{modules.map(([icon, title, href, description, action], index) => <Link className={index < 4 ? "module-priority" : "module-secondary"} href={href} key={title}>
        <div className="module-topline"><span className="module-icon" aria-hidden="true">{icon}</span><span className="module-state">Disponível</span></div><h2>{title}</h2><p>{description}</p><strong className="module-action">{action} →</strong>
      </Link>)}</div></section>
    <section className="future-modules"><span className="eyebrow">Próximos módulos</span><div>{future.map((item) => <span key={item}>{item}<small className="future-badge">Em desenvolvimento</small></span>)}</div></section>
  </main>;
}
