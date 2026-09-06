"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const response = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: data.get("email"), password: data.get("password"),
        organization_slug: data.get("organization_slug"),
      }),
    });
    if (!response.ok) return setError("Não foi possível autenticar com os dados informados.");
    router.push("/");
  }
  return <main className="login-page">
    <section className="login-brand-panel">
      <div><div className="brand"><span className="brand-mark">OT</span><span><strong>Ora <span>Tributa</span></strong><small>Inteligência Fiscal</small></span></div>
        <h1>Decisão tributária com <span>evidência.</span></h1>
        <p>Uma plataforma nacional para consulta, cobertura normativa, auditoria e planejamento — com regras versionadas e resultados reproduzíveis.</p></div>
      <small>Ambiente de desenvolvimento · nenhuma regra é inferida pela interface</small>
    </section>
    <section className="login-form-panel"><div className="login-card">
      <span className="eyebrow">Acesso seguro</span><h2>Entrar na plataforma</h2>
      <p>Informe seu usuário e a organização governada.</p>
      <form onSubmit={submit} className="stack-form">
        <label>E-mail<input name="email" type="email" autoComplete="username" required /></label>
        <label>Organização<input name="organization_slug" placeholder="governanca-tecnica-dev" required /></label>
        <label>Senha<input name="password" type="password" autoComplete="current-password" required /></label>
        {error && <p role="alert" className="curation-warning">{error}</p>}
        <button type="submit">Entrar</button>
      </form>
    </div></section>
  </main>;
}
