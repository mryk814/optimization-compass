/**
 * Reader-facing framing of each explorable. This mirrors
 * `src/optimization_compass/resources/explorables.json`, which is the authority;
 * `explorable.test.tsx` fails when the two drift apart.
 */
import type { SceneBeat } from "./scene";

export interface ExplorableMeta {
  question: string;
  fixedConditions: string;
  notImplied: string;
  /** Guided scene (ADR 0018). Empty when the figure has none. */
  beats: readonly SceneBeat[];
}

export const EXPLORABLE_META: Readonly<Record<string, ExplorableMeta>> = {
  "branch-bound-proof": {
    question: "良い組合せが見つかったあと、何を確かめれば最適だと言えるのか。",
    fixedConditions: "各品を一つまで選ぶ0-1ナップサック。入門は容量8、A・D・B・Cの（重さ, 得点）が（4, 8）・（2, 4）・（3, 5）・（5, 6）。発展は容量10でE（4, 6）・F（5, 7）・G（3, 3）・H（2, 1）を追加する。分数ナップサックで各候補の上界を計算する。絵の大きさは重さを表さない。",
    notImplied: "4品と8品で証明の仕組みを示す。大規模問題の速度や、一定の計算予算内での最適性保証、実務モデルが現実を正しく表すことは示さない。",
    beats: [],
  },
  "gradient-descent-valley": {
    question: "同じ更新式でも、learning rateと谷の細長さで、収束・遅い収束・振動・発散が切り替わるのはなぜか。",
    fixedConditions: "目的関数は f(x,y)=(x-1)^2+κ(y+2)^2 に固定し、勾配は解析式で厳密に与える。",
    notImplied: "一般的な手法の優劣や、実問題で良いlearning rateを示すものではない。",
    beats: [
      {
        settings: { method: "gd", eta: 0.02, kappa: 20 },
        durationS: 8,
        captionJa: "ηが小さいと、急なy方向はすぐ落ち着くが、ゆるやかなx方向は1回に4%しか縮まず、100回でも収束しない。",
        narrationJa: "学習率イータが小さいと、急なワイ方向はすぐに落ち着きます。けれど、ゆるやかなエックス方向は一回に四パーセントしか縮まず、百回たっても収束しません。",
      },
      {
        settings: { method: "gd", eta: 0.045, kappa: 20 },
        durationS: 8,
        captionJa: "ηを上げるとx方向は速くなるが、y方向は符号を変えて往復し始める。",
        narrationJa: "イータを上げると、エックス方向は速くなります。その代わり、急なワイ方向では一歩が行き過ぎて、谷を左右に往復し始めます。",
      },
      {
        settings: { method: "gd", eta: 0.053, kappa: 20, x0: 5, y0: -1.5 },
        durationS: 7,
        captionJa: "安定限界 1/κ = 0.05 を少しでも超えると、y方向の往復が毎回広がって発散する。",
        narrationJa: "イータが安定限界の〇・〇五をわずかに超えただけで、往復の幅は毎回広がり、発散します。限界を決めたのは、いちばん急な方向でした。",
      },
      {
        settings: { method: "gd", eta: 0.3, kappa: 2 },
        durationS: 7,
        captionJa: "谷が丸い（κが小さい）と限界が広がり、大きなηで両方向とも速く縮む。",
        narrationJa: "谷が丸くなると、安定限界が広がります。大きなイータが使えて、どちらの方向も数回で縮みます。",
      },
      {
        settings: { method: "momentum", eta: 0.02, kappa: 20, beta: 0.6 },
        durationS: 8,
        captionJa: "細長い谷のままでも、Momentumは直前の動きを持ち越して、ゆるやかな方向を加速する。",
        narrationJa: "細長い谷のままでも、モメンタムは直前の動きを持ち越すことで、ゆるやかなエックス方向を加速できます。",
      },
    ],
  },
  "lp-vertex-walk": {
    question: "線形目的の最適解が、なぜ実行可能領域の頂点だけを調べれば見つかるのか。",
    fixedConditions: "2変数・2本の不等式と非負制約からなる固定のLP（max 3x+2y の係数を動かす）。",
    notImplied: "実際のprimal simplex実装のpivot ruleや計算量を示すものではない。隣の頂点へ移る動きは教育用の模式化である。",
    beats: [],
  },
  "convexity-chord": {
    question: "関数が凸であるとは、グラフ上の任意の2点を結ぶ線分がグラフより下へ入らないことだと、どう確かめられるか。",
    fixedConditions: "1変数の3つの固定関数を使い、点a・bと混合比θを動かして定義の不等式を数値で確かめる。",
    notImplied: "有限個の点の確認は凸性の証明ではない。可行集合の凸性も別に確認が必要である。",
    beats: [],
  },
  "least-squares-bowl": {
    question: "残差の二乗和が最小の直線は、パラメータの平面ではどこにあり、1点を動かすとなぜ大きく動くのか。",
    fixedConditions: "t=0,1,2,3 の4点に直線 y=x₁+x₂t を当てはめる。観測の y だけを動かせ、重みはすべて等しい。",
    notImplied: "外れ値の扱い方や、実データで直線モデルが妥当かどうかは示さない。お椀の形はこの4点のtの並びで決まる。",
    beats: [
      {
        settings: { mode: "manual", a: 0.5, b: 1.3 },
        durationS: 9,
        captionJa: "どの直線にも、点との縦のずれ（残差）が残る。四角の面積が残差の二乗で、この直線では合計1.66になる。",
        narrationJa: "どの直線を引いても、点との縦のずれ、つまり残差が残ります。四角の面積が残差の二乗で、この直線では合計が一・六六です。右の平面では、この直線が一つの点になります。",
      },
      {
        settings: { mode: "fit" },
        durationS: 9,
        captionJa: "合計が最小の直線は y=0.9+0.9t で、二乗和は0.70。右のお椀の底にあたり、残差の合計もtを掛けた合計も0になる。",
        narrationJa: "合計が最小になる直線は、ワイ イコール 〇・九 たす 〇・九 ティーで、二乗和は〇・七〇です。右のお椀の底にあたり、残差の合計も、ティーを掛けた合計も、ちょうどゼロになります。",
      },
      {
        settings: { mode: "fit", y3: 8 },
        durationS: 10,
        captionJa: "4つ目の点を8へ上げると、最小の直線は y=0.1+2.1t へ傾く。二乗は大きな残差ほど強く効くので、1点が全体を引っ張る。",
        narrationJa: "四つ目の点を八まで上げると、最小の直線は、傾き二・一まで起き上がります。二乗は大きな残差ほど強く効くので、一つの点が直線全体を引っ張るのです。",
      },
    ],
  },
  "adam-step-ratio": {
    question: "Adamの一歩は、勾配の大きさが座標ごとに大きく違っても、なぜどの座標でもおよそη以下に収まり、どんなときに縮むのか。",
    fixedConditions: "目的関数は f(x,y)=(x-1)^2+20(y+2)^2、初期点は(4,3)、β2=0.999、ε=1e-8に固定する。ノイズは固定seedの正規乱数で、120歩まで計算する。",
    notImplied: "ニューラルネットワークの学習でのAdamの性能、汎化、良いlearning rateを示すものではない。勾配降下法との優劣も示さない。",
    beats: [
      {
        settings: { eta: 0.1, noise: 0, beta1: 0.9, compare: "none" },
        durationS: 9,
        captionJa: "最初の数歩は、勾配がxで6、yで200と33倍違っても、どちらの座標もη=0.1ずつ動く。点は最急降下の向きではなく、斜め45°に進む。",
        narrationJa: "最初の数歩では、勾配がエックスで六、ワイで二百と、三十三倍も違います。それでも、どちらの座標も〇・一ずつ動きます。だから点は、最も急な下り方向ではなく、斜め四十五度に進みます。",
      },
      {
        settings: { eta: 0.1, noise: 0, beta1: 0.9, compare: "gd" },
        durationS: 8,
        captionJa: "同じη=0.1の勾配降下法（灰色）は、一歩目でyが3から−17へ飛び、発散する。Adamのηは勾配に掛ける係数ではなく、一歩の長さに近い。",
        narrationJa: "同じイータ〇・一の勾配降下法は、一歩目でワイが三からマイナス十七へ飛び、発散します。アダムのイータは、勾配に掛ける係数ではなく、一歩の長さに近い量なのです。",
      },
      {
        settings: { eta: 0.2, noise: 0, beta1: 0.9, compare: "none" },
        durationS: 9,
        captionJa: "η=0.2ではyが谷底を越えて−2.4まで行き過ぎる。往復で勾配の符号がそろわなくなると、yの比 m̂/√v̂ は0へ縮む。",
        narrationJa: "イータを〇・二にすると、ワイは谷底を越えて、マイナス二・四まで行き過ぎます。往復するうちに勾配の符号がそろわなくなり、ワイの比は、ゼロに向かって縮んでいきます。",
      },
      {
        settings: { eta: 0.1, noise: 20, beta1: 0.9, compare: "none" },
        durationS: 9,
        captionJa: "勾配にσ=20のノイズを足すと、勾配の小さいxでは符号がそろわず、比がyより小さくなる。xはなかなか最小点へ近づかない。",
        narrationJa: "勾配に、標準偏差二十のノイズを足します。もともと勾配の小さいエックスでは符号がそろわず、比がワイよりずっと小さくなります。エックスは、なかなか最小点へ近づきません。",
      },
    ],
  },
  "bayes-opt-acquisition": {
    question: "ベイズ最適化は、予測が良い場所と分からない場所のどちらを次に測るかを、どう決めているのか。",
    fixedConditions: "区間[0,1]の固定の1次元関数、初期点 x=0.1, 0.45, 0.6、ノイズなし。Gaussian processはRBFカーネルで長さの尺度を固定し、獲得関数は201点の格子で最小化する。",
    notImplied: "ベイズ最適化の一般的な性能、他手法との優劣、実問題で良いβや長さの尺度を示すものではない。実務では長さの尺度をデータから推定する。",
    beats: [
      {
        settings: { acquisition: "lcb", beta: 0, lengthScale: 0.1, truth: "show" },
        durationS: 10,
        captionJa: "β=0は予測平均だけで選ぶ。x≈0.36の浅い谷に吸い寄せられて同じ点を測り続け、右の深い谷を一度も調べない。",
        narrationJa: "ベータがゼロだと、予測平均だけで次の点を選びます。〇・三六あたりの浅い谷に吸い寄せられて、同じ点を測り続け、右にある深い谷は一度も調べません。",
      },
      {
        settings: { acquisition: "lcb", beta: 2, lengthScale: 0.1, truth: "show" },
        durationS: 10,
        captionJa: "β=2では、不確実性の大きい右端や x=0.8 も試す。そこで下がる気配をつかみ、7回目の選択で x=0.84 の深い谷に着く。",
        narrationJa: "ベータを二にすると、不確実性の大きい右端や、〇・八のあたりも試します。そこで値が下がる気配をつかみ、七回目の選択で、〇・八四の深い谷に着きます。",
      },
      {
        settings: { acquisition: "lcb", beta: 8, lengthScale: 0.1, truth: "show" },
        durationS: 10,
        captionJa: "β=8では探索に寄りすぎ、端や観測の間を順に埋めていく。深い谷に着くのは9回目の選択になる。",
        narrationJa: "ベータを八まで上げると、探索に寄りすぎます。端や、観測と観測の間を順番に埋めていき、深い谷に着くのは九回目の選択です。",
      },
      {
        settings: { acquisition: "lcb", beta: 2, lengthScale: 0.15, truth: "show" },
        durationS: 10,
        captionJa: "長さの尺度を0.15と長めに置くと、観測の間も滑らかにつながると思い込み、σが小さく出る。深い谷を見落とし、x≈0.36に留まる。",
        narrationJa: "長さの尺度を〇・一五と長めに置くと、モデルは観測の間も滑らかにつながっていると思い込み、不確実性を小さく見積もります。その結果、深い谷を見落とし、〇・三六に留まります。",
      },
      {
        settings: { acquisition: "ei", beta: 2, lengthScale: 0.1, truth: "show" },
        durationS: 10,
        captionJa: "Expected Improvementは、最良値をどれだけ下回りそうかの期待値で選ぶ。βを決めなくても探索と活用が混ざり、8回目の選択で深い谷に着く。",
        narrationJa: "エクスペクテッド・インプルーブメントは、いまの最良値をどれだけ下回りそうかの期待値で選びます。ベータを決めなくても探索と活用が混ざり、八回目の選択で深い谷に着きます。",
      },
    ],
  },
};
