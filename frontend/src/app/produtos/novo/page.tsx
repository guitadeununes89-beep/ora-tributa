import Link from "next/link";
import { ProductForm } from "./product-form";

export default function NewProductPage() {
  return <main className="narrow-page">
    <Link href="/produtos" className="back-link">← Produtos</Link>
    <span className="eyebrow">Novo cadastro</span><h1>Produto</h1>
    <ProductForm />
  </main>;
}
