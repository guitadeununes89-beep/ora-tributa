import Link from "next/link";
import { Suspense } from "react";
import { AuthSummary } from "@/components/auth-summary";
import { AssistedConsultation } from "./assisted-consultation";

export default function ConsultationPage() {
  return <main className="management-page">
    <Link href="/" className="back-link">← Início</Link>
    <span className="eyebrow">Enquadramento assistido IBS/CBS</span>
    <h1>Consulta individual</h1>
    <p className="lead">Resultados dependem exclusivamente de regras publicadas e fatos suficientes.</p>
    <AuthSummary />
    <Suspense fallback={<p>Carregando consulta...</p>}>
      <AssistedConsultation />
    </Suspense>
  </main>;
}
