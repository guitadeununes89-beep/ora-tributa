export type SyntheticRuleVersion = {
  id: string;
  identity_code: string | null;
  version: number;
  lifecycle_status: string;
  valid_from: string;
  valid_to: string | null;
  legal_source_id: string | null;
  content_hash: string;
  published_at: string | null;
  rulesets?: string[];
};

export function CurationTable({ versions }: { versions: SyntheticRuleVersion[] }) {
  if (versions.length === 0) {
    return <p className="curation-empty">Nenhuma versão sintética cadastrada.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <caption>Snapshots sintéticos e estado de publicação</caption>
        <thead>
          <tr>
            <th>Identidade</th><th>Versão</th><th>Status</th><th>Vigência</th>
            <th>Fonte</th><th>Hash</th><th>Ruleset</th><th>Publicação</th>
          </tr>
        </thead>
        <tbody>
          {versions.map((item) => (
            <tr key={item.id}>
              <td>{item.identity_code ?? item.id}</td>
              <td>{item.version}</td>
              <td><span className={`status status-${item.lifecycle_status.toLowerCase()}`}>{item.lifecycle_status}</span></td>
              <td>{item.valid_from} → {item.valid_to ?? "sem término"}</td>
              <td>{item.legal_source_id ?? "não informada"}</td>
              <td><code title={item.content_hash}>{item.content_hash.slice(0, 12)}…</code></td>
              <td>{item.rulesets?.join(", ") || "—"}</td>
              <td>{item.published_at ? new Date(item.published_at).toLocaleString("pt-BR") : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

