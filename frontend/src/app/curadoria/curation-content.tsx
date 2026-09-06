"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { CurationTable, type SyntheticRuleVersion } from "./curation-table";

export function CurationContent() {
  const [versions, setVersions] = useState<SyntheticRuleVersion[]>([]);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    void apiFetch("/admin/tax-rule-versions").then(async (response) => {
      if (response.ok) setVersions((await response.json()) as SyntheticRuleVersion[]);
      else setUnavailable(true);
    }).catch(() => setUnavailable(true));
  }, []);
  return (
    <>
      {unavailable && (
        <p className="curation-warning" role="alert">
          Curadoria indisponível para esta sessão ou papel. Verifique a API e suas permissões.
        </p>
      )}
      <CurationTable versions={versions} />
    </>
  );
}

