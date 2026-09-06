import Link from "next/link";
import { AuthSummary } from "@/components/auth-summary";
import { CoverageDashboard } from "./coverage-dashboard";

export default function CoveragePage() {
  return <main className="coverage-page">
    <Link href="/" className="back-link">← Dashboard</Link>
    <span className="eyebrow">Reforma Tributária · mapa nacional</span>
    <h1>Cobertura normativa IBS/CBS</h1>
    <p className="lead">Visão integral do catálogo oficial, separando classificação técnica,
      mapeamento jurídico, especificação e regra executável.</p>
    <AuthSummary />
    <CoverageDashboard />
  </main>;
}
