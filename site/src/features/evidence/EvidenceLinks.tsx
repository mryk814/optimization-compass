import { Link } from "react-router-dom";

import { findEntity } from "../../contracts/entity-links";
import { useEntityLinks } from "../../state/entity-links";

export function EvidenceLinks({ sourceIds }: { sourceIds: readonly string[] }) {
  const links = useEntityLinks();
  const uniqueIds = [...new Set(sourceIds)];
  if (uniqueIds.length === 0) return null;
  return (
    <span className="evidence-links" aria-label="根拠資料">
      {uniqueIds.map((sourceId) => {
        const source = links.status === "ready" ? findEntity(links.index, "source", sourceId) : undefined;
        return (
          <Link key={sourceId} to={source?.canonical_url ?? `/sources/${sourceId}`}>
            {source?.label ?? "根拠"} <code>{sourceId}</code>
          </Link>
        );
      })}
    </span>
  );
}
