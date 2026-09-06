"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

export type SpecificationReadiness = {
  readiness: "READY_FOR_IMPLEMENTATION" | "NOT_READY";
  rule_id: string | null;
  specification_version: number | null;
  title: string | null;
  status: string | null;
  responsible_party: string | null;
  legal_source_id: string | null;
  catalog_version_id: string | null;
  cst: string | null;
  cclasstrib: string | null;
  effective_from: string | null;
  effective_to: string | null;
  issues: { code: string; path: string; message: string }[];
  disclaimer: string;
};

export function SpecificationReadinessContent() {
  const [specifications, setSpecifications] = useState<SpecificationReadiness[]>([]);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    void apiFetch("/admin/tax-rule-specifications")
      .then(async (response) => {
        if (response.ok) {
          setSpecifications((await response.json()) as SpecificationReadiness[]);
        } else {
          setUnavailable(true);
        }
      })
      .catch(() => setUnavailable(true));
  }, []);

  return (
    <section className="specification-section" aria-labelledby="specification-title">
      <h2 id="specification-title">Especificações jurídicas</h2>
      <p>
        O readiness confirma completude estrutural e referências governadas; não valida a
        interpretação jurídica.
      </p>
      {unavailable ? (
        <p className="curation-warning" role="alert">
          Pre-flight indisponível para esta sessão ou papel.
        </p>
      ) : (
        <SpecificationReadinessTable specifications={specifications} />
      )}
    </section>
  );
}

export function SpecificationReadinessTable({
  specifications,
}: {
  specifications: SpecificationReadiness[];
}) {
  if (specifications.length === 0) {
    return (
      <p className="curation-empty">
        Nenhuma especificação jurídica real foi cadastrada. As cinco posições piloto permanecem
        reservadas e sem conteúdo tributário.
      </p>
    );
  }
  return (
    <div className="table-wrap">
      <table>
        <caption>Prontidão documental para implementação</caption>
        <thead>
          <tr>
            <th>Regra</th>
            <th>Status</th>
            <th>Readiness</th>
            <th>Responsável</th>
            <th>Catálogo</th>
            <th>CST / cClassTrib</th>
            <th>Fonte</th>
            <th>Vigência</th>
            <th>Problemas</th>
          </tr>
        </thead>
        <tbody>
          {specifications.map((item) => (
            <tr key={item.rule_id + "-" + item.specification_version}>
              <td>
                <strong>{item.rule_id ?? "Documento inválido"}</strong>
                <br />
                <small>{item.title ?? "Sem título"}</small>
              </td>
              <td>{item.status ?? "—"}</td>
              <td>
                <span
                  className={
                    item.readiness === "READY_FOR_IMPLEMENTATION"
                      ? "status status-ready"
                      : "status status-not-ready"
                  }
                >
                  {item.readiness}
                </span>
              </td>
              <td>{item.responsible_party ?? "—"}</td>
              <td>{item.catalog_version_id ?? "—"}</td>
              <td>
                {item.cst ?? "—"} / {item.cclasstrib ?? "não aplicável"}
              </td>
              <td>{item.legal_source_id ?? "—"}</td>
              <td>
                {item.effective_from ?? "—"} → {item.effective_to ?? "sem término"}
              </td>
              <td>
                {item.issues.length === 0 ? (
                  "Nenhum problema estrutural"
                ) : (
                  <ul>
                    {item.issues.map((issue) => (
                      <li key={issue.code + "-" + issue.path}>
                        <code>{issue.code}</code>: {issue.path}
                      </li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

