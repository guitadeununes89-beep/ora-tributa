import Link from "next/link";
import { Suspense } from "react";
import { AuthSummary } from "@/components/auth-summary";
import { AssistedConsultationZfm } from "./assisted-consultation-zfm";

export default function ConsultationZfmPage() {
  return <main className="management-page">
    <Link href="/" className="back-link">← Início</Link>
    <span className="eyebrow">Enquadramento assistido IBS/CBS</span>
    <h1>Consulta — Zona Franca de Manaus</h1>
    <p className="lead">Resultados dependem exclusivamente de regras publicadas e fatos suficientes.</p>
    <AuthSummary />
    <Suspense fallback={<p>Carregando consulta...</p>}>
      <AssistedConsultationZfm />
    </Suspense>
  </main>;
}
