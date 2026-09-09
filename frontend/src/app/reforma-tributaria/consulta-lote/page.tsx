import Link from "next/link";
import { Suspense } from "react";
import { AuthSummary } from "@/components/auth-summary";
import { BatchConsultation } from "./batch-consultation";

export default function BatchConsultationPage() {
  return <main className="management-page">
    <Link href="/" className="back-link">← Início</Link>
    <span className="eyebrow">Enquadramento assistido IBS/CBS</span>
    <h1>Consulta em lote</h1>
    <p className="lead">
      Envie uma planilha com até algumas centenas de itens e receba, por linha, o mesmo
      resultado da consulta unificada — sem cálculo financeiro e sem publicar regra nova.
    </p>
    <AuthSummary />
    <Suspense fallback={<p>Carregando consulta em lote...</p>}>
      <BatchConsultation />
    </Suspense>
  </main>;
}
