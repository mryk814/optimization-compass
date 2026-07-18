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
      <p className="eyebrow">ページが見つかりません</p>
      <h1>ページが見つかりません</h1>
      <p>{detail}</p>
      <div className="not-found-actions">
        <Link className="text-link" to="/">
          Atlasへ戻る
        </Link>
        <Link className="text-link" to="/map">
          問題構造を見る
        </Link>
      </div>
    </section>
  );
}
