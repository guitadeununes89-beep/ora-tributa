import Link from "next/link";
import { AuthSummary } from "@/components/auth-summary";
import { ProductList } from "./product-list";

export default function ProductsPage() {
  return <main className="management-page">
    <Link href="/" className="back-link">← Início</Link>
    <span className="eyebrow">Cadastro versionado</span>
    <h1>Produtos</h1>
    <p className="lead">Dados cadastrais e histórico tributariamente relevante por organização.</p>
    <AuthSummary />
    <Link href="/produtos/novo" className="curation-link">Cadastrar produto →</Link>
    <ProductList />
  </main>;
}
