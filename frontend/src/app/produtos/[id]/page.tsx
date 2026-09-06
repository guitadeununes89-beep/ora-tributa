import Link from "next/link";
import { ProductDetail } from "./product-detail";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <main className="management-page">
    <Link href="/produtos" className="back-link">← Produtos</Link>
    <ProductDetail productId={id} />
  </main>;
}
