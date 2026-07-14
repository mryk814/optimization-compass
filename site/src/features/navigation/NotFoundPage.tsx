import { Link } from "react-router-dom";

export class EntityNotFoundError extends Error {
  constructor(entityLabel: string, entityId: string) {
    super(`${entityLabel}「${entityId}」は見つかりません。`);
    this.name = "EntityNotFoundError";
  }
}

type NotFoundPageProps = {
  detail?: string;
};

export function NotFoundPage({
  detail = "指定されたアトラスの経路は存在しません。",
}: NotFoundPageProps) {
  return (
    <section className="page-panel not-found-page">
      <p className="eyebrow">Not Found</p>
      <h1>ページが見つかりません</h1>
      <p>{detail}</p>
      <div className="not-found-actions">
        <Link className="text-link" to="/">
          Atlasへ戻る
        </Link>
        <Link className="text-link" to="/map">
          Mapを見る
        </Link>
      </div>
    </section>
  );
}
