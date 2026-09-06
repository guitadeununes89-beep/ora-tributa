import Link from "next/link";
import { AuthSummary } from "@/components/auth-summary";
import { ClassificationCatalog } from "./classification-catalog";

export default function ClassificationPage() {
  return (
    <main className="curation-page">
      <Link href="/" className="back-link">← Início</Link>
      <section aria-labelledby="classification-title">
        <span className="eyebrow">Reforma Tributária · fonte oficial versionada</span>
        <h1 id="classification-title">CST IBS/CBS e cClassTrib</h1>
        <p className="lead">
          Consulta ao catálogo normativo publicado. O conteúdo abaixo não determina
          automaticamente a tributação de produtos, operações ou NCMs.
        </p>
      </section>
      <AuthSummary />
      <ClassificationCatalog />
    </main>
  );
}
