export const PHYSICAL_SCENES = [
  {
    id: "topology", title: "荷重を支える形を、材料から見つける",
    question: "同じ力を支えるとき、材料をどこに残せば変形を小さくできるか。",
    description: "3D有限要素法で変形を求め、材料の配置を更新する過程を見ます。",
    article: "/learn/topology-optimization", articleLabel: "トポロジー最適化を読む",
  },
  {
    id: "arm", title: "腕全体で障害物を避けて、目標へ届く",
    question: "手先だけでなく腕全体をぶつけずに、短く、滑らかに動かすにはどうするか。",
    description: "同じ始点と終点で、移動距離と滑らかさの重みを変えた軌道を見比べます。",
    article: "/learn/concept.constrained-nlp", articleLabel: "制約付き非線形計画を読む",
  },
  {
    id: "drone", title: "未来を予測して、次の一手だけを実行する",
    question: "未来の軌道を毎回解き直すと、実際の飛行はどう決まるか。",
    description: "3D並進モデルのMPCで、未来の予測と実行した軌道を重ねます。",
    article: "/learn/concept.optimal-control", articleLabel: "最適制御を読む",
  },
] as const;
export type PhysicalSceneId = typeof PHYSICAL_SCENES[number]["id"];

export function physicalSceneRoute(id: string) { return `/theater/physical/${id}`; }
