-- Add natural gradient, SARAH, Muon and Lion under MF_STOCHASTIC_ML
-- (editorial scope TOPIC_NATURAL_GRADIENT / TOPIC_SARAH / TOPIC_MUON / TOPIC_LION).
-- Natural gradient is placed in MF_STOCHASTIC_ML (online learning on a statistical model), not MF_MANIFOLD.
-- Muon originates in a 2024 blog post; it is cited through the author's official repository,
-- the PyTorch documentation and the Moonshot AI report, not through the blog post.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S117', 'original_paper',
  'Natural Gradient Works Efficiently in Learning',
  'Shun-ichi Amari', '1998-02-01', '2026-10-10',
  'https://direct.mit.edu/neco/article/10/2/251/6143/Natural-Gradient-Works-Efficiently-in-Learning',
  'Natural gradient: steepest descent in the Riemannian metric given by the Fisher information matrix; online natural gradient learning is asymptotically Fisher efficient.',
  'primary', 'Original natural gradient paper. Neural Computation 10(2):251-276, 1998, DOI 10.1162/089976698300017746. Bibliographic metadata confirmed on 2026-10-10 against the MIT Press listing via search; the full text was not accessible. The abstract confirms that online natural-gradient learning is Fisher efficient (asymptotically equal to optimal batch estimation), proposes an adaptive learning rate, and suggests plateaus may weaken; guarantee wording confirmed against the published abstract.',
  'historical_primary'
),
(
  'S118', 'original_paper',
  'SARAH: A Novel Method for Machine Learning Problems Using Stochastic Recursive Gradient',
  'Lam M. Nguyen; Jie Liu; Katya Scheinberg; Martin Takac', '2017-08-01', '2026-10-10',
  'https://proceedings.mlr.press/v70/nguyen17b.html',
  'SARAH: recursive stochastic gradient estimate without storing past gradients for finite-sum problems; linear convergence under strong convexity.',
  'primary', 'Original SARAH paper. Proceedings of the 34th International Conference on Machine Learning (ICML 2017), PMLR 70:2613-2621; also arXiv:1703.00102. Bibliographic metadata confirmed on 2026-10-10 against the PMLR listing via search.',
  'historical_primary'
),
(
  'S119', 'original_paper',
  'Symbolic Discovery of Optimization Algorithms',
  'Xiangning Chen; Chen Liang; Da Huang; Esteban Real; Kaiyuan Wang; Hieu Pham; Xuanyi Dong; Thang Luong; Cho-Jui Hsieh; Yifeng Lu; Quoc V. Le', '2023-12-01', '2026-10-10',
  'https://proceedings.nips.cc/paper_files/paper/2023/hash/9a39b4925e35cf447ccba8757137d84f-Abstract-Conference.html',
  'Lion (EvoLved Sign Momentum): optimizer found by program search that tracks only momentum and applies the sign of an interpolated update.',
  'primary', 'Original Lion paper. NeurIPS 2023 (37th Conference on Neural Information Processing Systems); official PDF at https://proceedings.nips.cc/paper_files/paper/2023/file/9a39b4925e35cf447ccba8757137d84f-Paper-Conference.pdf; preprint arXiv:2302.06675. Page numbers are intentionally not recorded (they were found only in a citing paper). Bibliographic metadata confirmed on 2026-10-10 against the NeurIPS proceedings listing via search.',
  'historical_primary'
),
(
  'S120', 'official_repository',
  'google/automl: lion',
  'Google Research', NULL, '2026-10-10',
  'https://github.com/google/automl/tree/master/lion',
  'Reference implementations of Lion in JAX/Optax, TensorFlow 2 and PyTorch.',
  'primary', 'Official repository of the Lion authors. Observed archived (read-only) by the owner on 2026-05-06 via search; the implementation remains as a reference.',
  'verified_current'
),
(
  'S121', 'official_repository',
  'KellerJordan/Muon',
  'Keller Jordan', NULL, '2026-10-10',
  'https://github.com/KellerJordan/Muon',
  'Muon: optimizer for the hidden weight matrices of neural networks, orthogonalizing the momentum update; other parameters are to be optimized with AdamW.',
  'primary', 'Official repository of the Muon author. Muon originates in a 2024 blog post by Keller Jordan (not peer-reviewed; not used as a source row). Kept as the reference implementation (NVIDIA emerging-optimizers code cites its muon.py). Its README was not read in the authoring session; existence confirmed on 2026-10-10 via search.',
  'verified_current'
),
(
  'S122', 'official_documentation',
  'torch.optim.Muon',
  'PyTorch', NULL, '2026-10-10',
  'https://docs.pytorch.org/docs/stable/generated/torch.optim.Muon.html',
  'Muon in PyTorch: optimizer for 2D hidden-layer parameters with Newton-Schulz orthogonalization; bias and embedding parameters should use a standard method such as AdamW; adjust_lr_fn modes follow the original and Moonshot implementations.',
  'primary', 'Official implementation documentation. Confirmed on 2026-10-10 via search: the page exists from PyTorch 2.9 through main with an identical signature (lr=0.001, weight_decay=0.1, momentum=0.95, nesterov=True, ns_steps=5, Newton-Schulz coefficients 3.4445, -4.775, 2.0315). The documented example applies Muon only to 2D parameters and AdamW to the rest.',
  'verified_current'
),
(
  'S123', 'original_paper',
  'Muon is Scalable for LLM Training',
  'Jingyuan Liu; Jianlin Su; Xingcheng Yao; Zhejun Jiang; Guokun Lai; Yulun Du; Yidao Qin; Weixin Xu; Enzhe Lu; Junjie Yan; Yanru Chen; Huabin Zheng; Yibo Liu; Shaowei Liu; Bohong Yin; Weiran He; Han Zhu; Yuzhi Wang; Jianzhou Wang; Mengnan Dong; Zheng Zhang; Yongsheng Kang; Hao Zhang; Xinran Xu; Yutao Zhang; Yuxin Wu; Xinyu Zhou; Zhilin Yang', '2025-02-24', '2026-10-10',
  'https://arxiv.org/abs/2502.16982',
  'Muon with weight decay and per-parameter update-scale adjustment scales to LLM training; reports about 2x compute efficiency versus AdamW.',
  'primary', 'Moonshot AI technical report, arXiv:2502.16982 (2025); preprint, not peer-reviewed. Defines the scaled Muon variant, not the origin of Muon. Confirmed on 2026-10-10 via search.',
  'historical_primary'
);

INSERT INTO methods (
  method_id, name_ja, name_en, aliases, method_family_id, method_level,
  summary, problem_classes, required_assumptions, derivative_information, variable_types, constraint_support,
  convex_fit, nonconvex_applicability, solution_scope, determinism, exactness, theoretical_guarantee,
  optimality_certificate, scalability, memory_tendency, per_iteration_cost, evaluation_pattern, parallelism,
  initialization_sensitivity, hyperparameter_sensitivity, scaling_sensitivity, noise_robustness, discontinuity_robustness, constraint_violation_handling,
  warm_start, online_use, strengths, weaknesses, typical_failures, avoid_conditions,
  first_choice_conditions, second_choice_conditions, switch_signals, beginner_level, tuning_difficulty, implementation_difficulty,
  explainability, stopping_criteria, diagnostic_metrics, related_method_ids, parent_method_id, child_method_ids,
  reference_source_ids, confidence, last_verified
) VALUES
(
  'M_NATURAL_GRADIENT', '自然勾配法', 'Natural gradient descent', 'natural gradient;natural gradient descent;自然勾配', 'MF_STOCHASTIC_ML', 'variant', '確率モデルのパラメータ空間のRiemann計量(Fisher情報行列)で勾配を補正し、座標の取り方に依存しにくい方向へ更新する。', 'machine_learning;statistical_estimation;neural_network;online_learning', 'パラメータ空間にFisher情報行列などのRiemann計量が定義でき、その逆(または近似)を作用させられること。', 'stochastic_gradient;fisher_information_matrix', 'continuous_high_dimensional', 'usually_unconstrained;simple_projection', 'unknown', 'unknown', 'local', 'stochastic', 'local_numerical', 'オンライン学習で漸近的にFisher効率を達成することが示されている(Amari 1998)。非凸学習での収束保証はこの出典では示されていない。', 'training_gradient_or_loss_not_global_certificate', 'limited_by_Fisher_matrix_size_without_approximation', 'high_Fisher_matrix_O_d2_unless_approximated', '勾配に加えてFisher情報行列(または近似)の構成と、その逆行列の作用(線形solve)。', '非常に多数の安価なstochastic steps。', 'unknown', 'unknown', 'high', 'designed_to_reduce_parameterization_dependence', 'unknown', 'low', 'projection_or_penalty', 'yes', 'yes', 'パラメータ化に依存しにくい更新;条件の悪い統計モデルでplain gradientより有利になりうる', 'Fisher情報行列の計算・保持・逆行列が高コスト;近似の選び方に依存', 'Fisher推定の誤差;dampingの不足;近似行列の不安定性', 'Fisher情報行列を定義・近似できない目的;パラメータ数が大きく近似も使えない場合', 'unknown', '確率モデルの最尤学習で、勾配降下の収束が座標のスケールや相関に強く左右される場合。', 'Fisher行列の条件数が極端;更新が不安定;計算費が支配的。', 'low', 'high', 'high', 'medium', 'validation_metric;natural_gradient_norm;epoch_budget', 'train_loss;validation_loss;natural_gradient_norm;fisher_condition_number;damping', 'M_SGD;M_RIEMANNIAN_GRADIENT', 'MF_STOCHASTIC_ML', '', 'S117', 'medium', '2026-10-10'
),
(
  'M_SARAH', 'SARAH（確率的再帰勾配法）', 'Stochastic recursive gradient algorithm', 'SARAH;stochastic recursive gradient', 'MF_STOCHASTIC_ML', 'variant', '内側ループで直前の勾配推定を再帰的に更新し、過去の勾配を保存せずに分散を抑える有限和向けの方法。', 'machine_learning;finite_sum_ERM', '有限和形式の目的。各項が滑らか。強凸のもとで線形収束(出典の主張範囲)。外側ループで全勾配を計算できること。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional', 'usually_unconstrained;simple_projection', 'strong_theory', 'unknown', 'local', 'stochastic', 'local_numerical', '強凸のとき線形収束が示されている(Nguyen et al. 2017)。非凸の保証はこの出典では確認していない。', 'training_gradient_or_loss_not_global_certificate', 'high', 'low_no_stored_per_sample_gradients', '内側ステップごとに1 sampleの勾配を現在点と直前点で各1回 + 外側ループごとの全勾配。', '外側ループで全勾配、内側ループで安価な再帰的stochastic steps。', 'unknown', 'unknown', 'medium', 'unknown', 'variance_reduction_for_finite_sum_sampling_noise', 'low', 'projection_or_penalty', 'yes', 'no', 'SAG/SAGAと違い過去の勾配を保存しない;内側ループの更新が安価', '外側ループごとに全勾配計算が必要;step sizeと内側ループ長の調整;内側ループの推定は偏りを持つ', '内側ループが長すぎて推定が劣化;step size過大でdivergence;plateau', '有限和でないstreaming目的;勾配が不正;非凸学習での保証が必要な場合(この出典では未確認)', 'unknown', '有限和の凸ERMで、SAGAの勾配テーブルを持てず、SVRGと同様の分散縮小を使いたい場合。', '内側ループでloss増加;全勾配計算費が支配的;SVRGやSGDと差が出ない。', 'low', 'medium', 'medium', 'medium', 'full_gradient_norm_tolerance;epoch_budget;validation_metric', 'train_loss;full_gradient_norm;learning_rate;inner_loop_length;seed_variance', 'M_SGD;M_SVRG;M_SAGA', 'MF_STOCHASTIC_ML', '', 'S118', 'medium', '2026-10-10'
),
(
  'M_MUON', 'Muon', 'Muon', 'Muon', 'MF_STOCHASTIC_ML', 'variant', '隠れ層の2次元重み行列に対し、momentum更新をNewton-Schulz反復で直交化してから適用する。他のパラメータは別のoptimizer(AdamW等)で更新する。', 'machine_learning;neural_network;llm_training', '2次元の重み行列(隠れ層)を対象とする。bias・embeddingなど他のパラメータはAdamW等の標準的な方法で最適化する(PyTorchドキュメント)。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional;matrix_parameters', 'usually_unconstrained;simple_projection', 'unknown', 'unknown', 'local', 'stochastic', 'local_numerical', '原典(Keller Jordan 2024のblog記事)は収束保証を与えていない。この出典群に保証は記載されていない。大規模学習での効率はMoonshot AIの報告(Liu et al. 2025, arXiv)にあるが経験的主張である。', 'training_gradient_or_loss_not_global_certificate', 'very_high_GPU_distributed', 'low_one_momentum_per_parameter', 'mini-batch forward/backward + momentum + 行列積によるNewton-Schulz反復(PyTorch既定のns_stepsはバージョン依存)。', '非常に多数の安価なstochastic steps。', 'high_GPU_data_model_parallel', 'unknown', 'high', 'unknown', 'unknown', 'low', 'projection_or_penalty', 'yes', 'yes', 'momentum 1個分のstateで行列重みの更新を直交化;大規模LLM学習でAdamW比の計算効率向上が報告されている(Liu et al. 2025)', '2次元の隠れ層重みにしか適用できず別のoptimizerとの併用が必要;Newton-Schulzの行列積による追加計算;収束保証が示されていない', '非2次元パラメータへの誤適用;学習率・weight decayの不整合(AdamWの設定をそのまま流用);divergence', '行列でないパラメータだけの問題;embedding・最終層・1次元パラメータ(bias等)への適用(別のoptimizerへ回す);厳密gap必須;勾配が不正', 'unknown', 'Transformer等の隠れ層重みが主要で、AdamWのstateメモリや収束速度を改善したい場合。', 'loss停滞;非行列パラメータの扱いで挙動が不安定;AdamWと比べ利得が出ない。', 'low', 'high', 'medium', 'medium', 'validation_metric;gradient_norm_estimate;epoch_budget;early_stopping', 'train_loss;validation_loss;gradient_norm;learning_rate;seed_variance', 'M_MOMENTUM_SGD;M_ADAMW', 'MF_STOCHASTIC_ML', '', 'S121;S122;S123', 'medium', '2026-10-10'
),
(
  'M_LION', 'Lion', 'Lion (EvoLved Sign Momentum)', 'Lion;EvoLved Sign Momentum', 'MF_STOCHASTIC_ML', 'variant', 'momentumのみを保持し、補間した更新方向の符号(sign)を使って座標ごとに一定の大きさで更新する。プログラム探索で発見された。', 'machine_learning;neural_network', '有用なstochastic gradient。学習率はAdamWより小さくweight decayを大きくする調整が通例(Keras docsの目安は学習率が3-10倍小さい)。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional', 'usually_unconstrained;simple_projection', 'unknown', 'unknown', 'local', 'stochastic', 'local_numerical', '原典(Chen et al. 2023)はプログラム探索による経験的な発見であり、一般的な収束保証はこの出典では示されていない。', 'training_gradient_or_loss_not_global_certificate', 'very_high_GPU_distributed', 'low_one_momentum_per_parameter', 'one mini-batch forward/backward + momentumとsign演算。', '非常に多数の安価なstochastic steps。', 'high_GPU_data_model_parallel', 'unknown', 'high', 'sign_update_ignores_gradient_magnitude', 'unknown', 'low', 'projection_or_penalty', 'yes', 'yes', 'Adamより少ないメモリ(momentumのみ);更新の大きさが座標間で揃う', '学習率・weight decayをAdamWから再調整する必要;勾配の大きさ情報を使わない;収束保証が示されていない', 'divergence(学習率過大);plateau;AdamWの設定の流用による不調', '厳密gap必須;勾配が不正;小batchで符号が不安定な場合', 'unknown', 'Adamのstateメモリを減らしたい大規模NN学習。', 'validation悪化;loss停滞;AdamWと比べ利得が出ない。', 'low', 'high', 'low_with_framework', 'medium', 'validation_metric;gradient_norm_estimate;epoch_budget;early_stopping', 'train_loss;validation_loss;gradient_norm;learning_rate;seed_variance', 'M_ADAM;M_ADAMW;M_MOMENTUM_SGD', 'MF_STOCHASTIC_ML', '', 'S119;S120;S047;S049', 'medium', '2026-10-10'
);

UPDATE methods
SET child_method_ids = 'M_SGD;M_MOMENTUM_SGD;M_ADAM;M_ADAMW;M_ADAGRAD;M_RMSPROP;M_SVRG;M_SAGA;M_NATURAL_GRADIENT;M_SARAH;M_MUON;M_LION'
WHERE method_id = 'MF_STOCHASTIC_ML';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_STOCHASTIC_ML_NATURAL_GRADIENT', 'MF_STOCHASTIC_ML', 'M_NATURAL_GRADIENT', 'is_a', 1, 'yes', 'Natural gradient learning is classified under Stochastic-gradient and ML optimization; its relation to Riemannian optimization is kept in related_method_ids.', 'S117', 'medium', '2026-10-10'),
('MH_STOCHASTIC_ML_SARAH', 'MF_STOCHASTIC_ML', 'M_SARAH', 'is_a', 1, 'yes', 'SARAH is classified under Stochastic-gradient and ML optimization.', 'S118', 'medium', '2026-10-10'),
('MH_STOCHASTIC_ML_MUON', 'MF_STOCHASTIC_ML', 'M_MUON', 'is_a', 1, 'yes', 'Muon is classified under Stochastic-gradient and ML optimization.', 'S121;S122;S123', 'medium', '2026-10-10'),
('MH_STOCHASTIC_ML_LION', 'MF_STOCHASTIC_ML', 'M_LION', 'is_a', 1, 'yes', 'Lion is classified under Stochastic-gradient and ML optimization.', 'S119;S120', 'medium', '2026-10-10');

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES
('TERM_NATURAL_GRADIENT', 'method', 'M_NATURAL_GRADIENT', '自然勾配法', 'Natural gradient', '[]',
 '["natural gradient descent","自然勾配"]', '["Fisher情報行列"]', '[]', '[]',
 'Riemann多様体上の一般的なRiemann勾配(M_RIEMANNIAN_GRADIENT)とは別項目。自然勾配は統計モデルのFisher計量を使う。', 'ja-JP,en',
 '自然勾配の呼称をmethodへ解決する。', '["S117"]', '2026-10-10'),
('TERM_SARAH', 'method', 'M_SARAH', 'SARAH法', 'Stochastic recursive gradient algorithm', '["SARAH"]',
 '["stochastic recursive gradient"]', '["分散縮小"]', '[]', '[]',
 'SVRG・SAGAとは別の手法。SARAHは再帰的な勾配推定を使い、過去の勾配を保存しない。', 'ja-JP,en',
 '略称と正式名をmethodへ解決する。', '["S118"]', '2026-10-10'),
('TERM_MUON', 'method', 'M_MUON', 'Muon法', 'Muon', '[]',
 '[]', '["行列重みの直交化"]', '[]', '[]',
 '素粒子のミューオンではなく最適化手法。Adam・AdamWとは別の手法で、隠れ層の行列重みを対象にする。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S121"]', '2026-10-10'),
('TERM_LION', 'method', 'M_LION', 'Lion法', 'Lion', '[]',
 '["EvoLved Sign Momentum"]', '["符号momentum"]', '[]', '[]',
 'Adam・AdamWとは別の手法。Lionはmomentumのsignで更新する。', 'ja-JP,en',
 '名称と正式名をmethodへ解決する。', '["S119"]', '2026-10-10');

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level, api_name,
  method_selector, implementation_notes, limitations, source_ids, confidence, last_verified
) VALUES
('MIM_STOCHASTIC_ML_MUON_PYTORCH', 'M_MUON', 'I_PYTORCH_OPTIM', 'native', 'torch.optim.Muon', '',
 '2次元パラメータ専用。bias・embeddingなどはAdamW等で別途最適化する。adjust_lr_fnで原実装方式とMoonshot方式(match_rms_adamw)を選べる。', 'PyTorch 2.9以降で利用可能(ドキュメントはmainまで同一signature)。2次元パラメータ専用で、embedding・最終層・1次元パラメータは別のoptimizerで更新する。既定値(lr=0.001, weight_decay=0.1, momentum=0.95, nesterov, ns_steps=5)はversionで確認。実装対応は一般的推奨を意味しない。', 'S122', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_LION_OPTAX', 'M_LION', 'I_OPTAX', 'native', 'optax.lion', '',
 'optimizer transformation library。training loop、schedule、regularization、state checkpointは利用者が管理。', '機能・status・optionはversionで確認。weight_decayの既定値がOptaxと原実装(google/automl)で異なるとの報告がある。実装対応は一般的推奨を意味しない。', 'S047', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_LION_KERAS', 'M_LION', 'I_TENSORFLOW_OPTIM', 'native', 'tf.keras.optimizers.Lion', '',
 '学習率はAdamWより3-10倍小さくする目安がKerasドキュメントにある。', '機能・status・optionはversionとbackendで確認。実装対応は一般的推奨を意味しない。', 'S049', 'medium', '2026-10-10');

UPDATE implementations SET supported_method_ids = supported_method_ids || ';M_MUON'
WHERE implementation_id = 'I_PYTORCH_OPTIM';
UPDATE implementations SET supported_method_ids = supported_method_ids || ';M_LION'
WHERE implementation_id IN ('I_OPTAX', 'I_TENSORFLOW_OPTIM');

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004205', 'S117', 'methods', 'M_NATURAL_GRADIENT', 'row', 'Fisher計量で補正した勾配方向へ更新する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004206', 'S118', 'methods', 'M_SARAH', 'row', '再帰的な勾配推定で過去の勾配を保存せず分散を抑える。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004207', 'S121', 'methods', 'M_MUON', 'row', '隠れ層行列重みのmomentum更新を直交化して適用する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004208', 'S122', 'methods', 'M_MUON', 'row', '隠れ層行列重みのmomentum更新を直交化して適用する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004209', 'S123', 'methods', 'M_MUON', 'row', '隠れ層行列重みのmomentum更新を直交化して適用する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004210', 'S119', 'methods', 'M_LION', 'row', 'momentumのsignで座標ごとに一定の大きさの更新を行う。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004211', 'S120', 'methods', 'M_LION', 'row', 'momentumのsignで座標ごとに一定の大きさの更新を行う。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004212', 'S047', 'methods', 'M_LION', 'row', 'momentumのsignで座標ごとに一定の大きさの更新を行う。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004213', 'S049', 'methods', 'M_LION', 'row', 'momentumのsignで座標ごとに一定の大きさの更新を行う。', 'supporting_or_primary', 'medium', '2026-10-10');
