import { Link, useParams } from "react-router-dom";
import { NotFoundPage } from "../navigation/NotFoundPage";
import { PHYSICAL_SCENES } from "./catalog";
import { ScenePlayer, useLoadedScene } from "./ScenePlayer";

export default function PhysicalScenePage() {
  const { sceneId = "" } = useParams();
  const meta = PHYSICAL_SCENES.find(scene => scene.id === sceneId);
  const { loaded, error } = useLoadedScene(meta?.id);
  if (!meta) return <NotFoundPage detail="この3D教材は登録されていません。" />;
  return <section className="atlas-page physical-page">
    <header className="atlas-page-header">
      <p className="eyebrow">記事の図を大きく見る</p>
      <h1>{meta.title}</h1>
      <p>{meta.description}</p>
    </header>
    <p><Link to={`${meta.article}?figure=${meta.id}`}>{meta.articleLabel} →</Link></p>
    <p className="ex-question"><span>見る問い</span>{meta.question}</p>
    {error && <p role="alert">{error}</p>}
    {loaded?.id === meta.id ? <ScenePlayer key={meta.id} scene={loaded} /> : !error && <p role="status">計算結果を読み込んでいます…</p>}
    <div className="physical-next"><Link to={`${meta.article}?figure=${meta.id}`}>{meta.articleLabel} →</Link><Link to="/theater">ほかの動きを見る →</Link></div>
  </section>;
}
