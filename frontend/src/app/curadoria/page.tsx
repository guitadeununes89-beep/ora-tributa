import Link from "next/link";
import { AuthSummary } from "@/components/auth-summary";
import { CurationContent } from "./curation-content";
import { SpecificationReadinessContent } from "./specification-readiness";

export default function CurationPage() {
  return (
    <main className="curation-page">
      <Link href="/" className="back-link">← Fundação</Link>
      <section aria-labelledby="curation-title">
        <span className="eyebrow">Governança normativa · sem interpretação automática</span>
        <h1 id="curation-title">Curadoria tributária</h1>
        <p className="lead">
          Prontidão documental e ciclo persistido de regras. Esta tela não interpreta legislação
          nem transforma especificações em código executável.
        </p>
      </section>
      <AuthSummary />
      <SpecificationReadinessContent />
      <CurationContent />
    </main>
  );
}