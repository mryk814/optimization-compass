import { findEntity } from "../../contracts/entity-links";
import type { AtlasStateV1 } from "../../state/atlas-state";
import { useEntityLinks } from "../../state/entity-links";
import { JourneyLink } from "../../state/journey-navigation";

export function EvidenceLinks({ atlasState, sourceIds }: { atlasState?: AtlasStateV1; sourceIds: readonly string[] }) {
  const links = useEntityLinks();
  const uniqueIds = [...new Set(sourceIds)];
  if (uniqueIds.length === 0) return null;
  return (
    <span className="evidence-links" aria-label="根拠資料">
      {uniqueIds.map((sourceId) => {
        const source = links.status === "ready" ? findEntity(links.index, "source", sourceId) : undefined;
        return (
          <JourneyLink atlasState={atlasState} key={sourceId} to={source?.canonical_url ?? `/sources/${sourceId}`}>
            {source?.label ?? "根拠"} <code>{sourceId}</code>
          </JourneyLink>
        );
      })}
    </span>
  );
}
