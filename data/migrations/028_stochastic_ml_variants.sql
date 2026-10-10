-- Add AdaGrad, RMSprop, SVRG and SAGA under MF_STOCHASTIC_ML
-- (editorial scope TOPIC_ADAGRAD / TOPIC_RMSPROP / TOPIC_SVRG / TOPIC_SAGA).
-- RMSprop originates in an unpublished lecture (Tieleman and Hinton, Coursera, 2012); it is cited
-- through the official PyTorch documentation and Graves (2013), not through a lecture source row.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S112', 'original_paper',
  'Adaptive Subgradient Methods for Online Learning and Stochastic Optimization',
  'John Duchi; Elad Hazan; Yoram Singer', '2011-07-01', '2026-10-10',
  'https://jmlr.org/papers/v12/duchi11a.html',
  'AdaGrad: per-coordinate adaptive step sizes from accumulated squared (sub)gradients, with regret bounds for online convex optimization.',
  'primary', 'Original AdaGrad paper. Journal of Machine Learning Research 12(61):2121-2159, July 2011. Bibliographic metadata confirmed on 2026-10-10 against the official JMLR listing via search.',
  'historical_primary'
),
(
  'S113', 'original_paper',
  'Accelerating Stochastic Gradient Descent using Predictive Variance Reduction',
  'Rie Johnson; Tong Zhang', '2013-12-01', '2026-10-10',
  'https://papers.nips.cc/paper/2013/hash/ac1dd209cbcc5e5d1c6e28598e8cbbe8-Abstract.html',
  'SVRG: snapshot full gradient as control variate reduces stochastic-gradient variance; geometric convergence for smooth strongly convex finite sums.',
  'primary', 'Original SVRG paper. Advances in Neural Information Processing Systems 26 (NIPS 2013), pp. 315-323. Bibliographic metadata confirmed on 2026-10-10 against the official proceedings listing via search.',
  'historical_primary'
),
(
  'S114', 'original_paper',
  'SAGA: A Fast Incremental Gradient Method With Support for Non-Strongly Convex Composite Objectives',
  'Aaron Defazio; Francis Bach; Simon Lacoste-Julien', '2014-12-01', '2026-10-10',
  'https://proceedings.neurips.cc/paper/2014/hash/ede7e2b6d13a41ddf9f4bdef84fdc737-Abstract.html',
  'SAGA: stored per-sample gradients as control variate; proximal support for composite objectives; convergence for strongly convex and non-strongly convex cases.',
  'primary', 'Original SAGA paper. Advances in Neural Information Processing Systems 27 (NIPS 2014), pp. 1646-1654; also arXiv:1407.0202. Bibliographic metadata confirmed on 2026-10-10 against the official proceedings listing via search.',
  'historical_primary'
),
(
  'S115', 'official_documentation',
  'torch.optim.RMSprop',
  'PyTorch', NULL, '2026-10-10',
  'https://docs.pytorch.org/docs/stable/generated/torch.optim.RMSprop.html',
  'RMSprop: running average of squared gradients scales the step; attributed to G. Hinton''s course; centered variant attributed to Graves (2013); eps is added after the square root (TensorFlow swaps the two).',
  'primary', 'Official implementation documentation. Authority for the implemented algorithm and options, not for the method''s origin: RMSprop originates in an unpublished lecture (Tieleman and Hinton, Coursera Neural Networks for Machine Learning, lecture 6.5, 2012), which is not peer-reviewed and has no source row here. Confirmed on 2026-10-10 via search.',
  'verified_current'
),
(
  'S116', 'original_paper',
  'Generating Sequences With Recurrent Neural Networks',
  'Alex Graves', '2013-08-01', '2026-10-10',
  'https://arxiv.org/abs/1308.0850',
  'Published description of the centered form of RMSprop (normalizing by the variance estimate of the gradient) used for sequence generation.',
  'primary', 'arXiv:1308.0850 (2013). Primary paper for the centered RMSprop variant; not the origin of plain RMSprop. Bibliographic metadata confirmed on 2026-10-10 via search.',
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
  'M_ADAGRAD', 'AdaGrad', 'Adaptive subgradient method (AdaGrad)', 'AdaGrad;Adagrad', 'MF_STOCHASTIC_ML', 'variant', '過去の勾配の二乗和を座標ごとに蓄え、その平方根で学習率を割ることで座標別にstepを調整する。', 'machine_learning;stochastic_ERM;online_convex_optimization;sparse_features', '凸なonline/stochastic目的でsubgradientまたは勾配が得られること。基本学習率(step size)の選択。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional', 'usually_unconstrained;simple_projection', 'strong_theory', 'unknown', 'local', 'stochastic', 'local_numerical', 'online凸最適化でregret境界(Duchi, Hazan, Singer 2011)。非凸のstationary保証はこの出典では示されていない。', 'training_gradient_or_loss_not_global_certificate', 'very_high_GPU_distributed', 'medium_one_accumulator_per_parameter', 'one mini-batch gradient + 座標別の二乗勾配累積。', '非常に多数の安価なstochastic steps。', 'unknown', 'unknown', 'high', '座標別適応により軽減される場合がある;出典の主張範囲を超えて一般化しない', 'designed_for_stochastic_noise_online_setting', 'low', 'projection_or_penalty', 'yes', 'yes', 'sparse特徴で稀な座標に大きなstepを与える;座標別step;online', '二乗勾配の累積が単調増加し有効学習率が減衰する;基本学習率に依存', 'learning_rate_decays_too_early;plateau;bad_base_learning_rate', '厳密gap必須;勾配が不正;長いnonconvex学習で有効学習率の過度な減衰が問題になる場合', 'unknown', 'sparseな特徴を持つ凸ERMやonline学習でSGDより座標別適応が欲しい場合。', 'train_loss停滞;有効学習率の過度な減衰;validation悪化。', 'medium', 'medium', 'low_with_framework', 'medium', 'validation_metric;gradient_norm_estimate;epoch_budget;early_stopping', 'train_loss;validation_loss;gradient_norm;learning_rate;seed_variance', 'M_SGD;M_ADAM', 'MF_STOCHASTIC_ML', '', 'S112;S047;S048;S049', 'medium', '2026-10-10'
),
(
  'M_RMSPROP', 'RMSprop', 'RMSprop', 'RMSprop;RMSProp', 'MF_STOCHASTIC_ML', 'variant', '二乗勾配の指数移動平均の平方根で学習率を割り、座標ごとにstepを調整する。centered形では勾配の分散推定で正規化する。', 'machine_learning;stochastic_ERM;neural_network', '有用なstochastic gradient、基本学習率、平滑化係数(alpha)とeps。実装ごとのepsの位置(平方根の後か前か)を確認する。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional', 'usually_unconstrained;simple_projection', 'unknown', 'unknown', 'local', 'stochastic', 'local_numerical', '原典(未刊行の講義: Tieleman and Hinton, Coursera Neural Networks for Machine Learning, lecture 6.5, 2012)は一般的な収束保証を与えていない。この出典群に保証は記載されていない。', 'training_gradient_or_loss_not_global_certificate', 'very_high_GPU_distributed', 'medium_one_moving_average_per_parameter;centered_adds_gradient_average', 'one mini-batch forward/backward + 座標別の二乗勾配移動平均。', '非常に多数の安価なstochastic steps。', 'high_GPU_data_model_parallel', 'unknown', 'high', 'unknown', 'designed_for_stochastic_noise', 'low', 'projection_or_penalty', 'yes', 'yes', '座標別step;mini-batch勾配の尺度差を吸収;実装が軽い', '原典に収束保証がない;学習率・alpha・epsに依存;epsの位置が実装で異なり結果が一致しない場合がある', 'divergence;plateau;bad_learning_rate;eps_convention_mismatch_between_frameworks', '厳密gap必須;勾配が不正;フレームワーク間でeps規約を揃えずに結果を比較する場合', 'unknown', '座標ごとに勾配の尺度が大きく異なるNN学習で、SGDの学習率調整が難しい場合。', 'validation悪化;gradient explosion;loss停滞;フレームワーク間で結果が不一致。', 'medium', 'high', 'low_with_framework', 'medium', 'validation_metric;gradient_norm_estimate;epoch_budget;early_stopping', 'train_loss;validation_loss;gradient_norm;learning_rate;seed_variance', 'M_SGD;M_ADAM;M_ADAGRAD', 'MF_STOCHASTIC_ML', '', 'S115;S116;S047;S048;S049', 'medium', '2026-10-10'
),
(
  'M_SVRG', 'SVRG（確率的分散縮小勾配法）', 'Stochastic variance reduced gradient', 'SVRG;stochastic variance reduced gradient', 'MF_STOCHASTIC_ML', 'variant', '定期的にスナップショット点での全勾配を計算し、確率的勾配を制御変量として補正することで更新の分散を抑える。', 'machine_learning;finite_sum_ERM', '有限和(finite-sum)形式の目的。各項が滑らか。強凸のもとで線形収束(出典の主張範囲)。epochごとに全勾配を計算できること。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional', 'usually_unconstrained;simple_projection', 'strong_theory', 'unknown', 'local', 'stochastic', 'local_numerical', '滑らかな強凸有限和で幾何的(線形)収束(Johnson and Zhang 2013)。非凸の保証はこの出典では示されていない。', 'training_gradient_or_loss_not_global_certificate', 'high', 'low_snapshot_and_full_gradient_O_d', '1 sampleの勾配を現在点とsnapshot点で各1回 + epochごとの全勾配(n sample分)。', 'epoch開始時に全勾配、内側ループで安価なstochastic steps。', 'unknown', 'unknown', 'medium', 'unknown', 'variance_reduction_for_finite_sum_sampling_noise', 'low', 'projection_or_penalty', 'yes', 'no', 'SGDより少ない分散で一定step sizeでも収束;追加メモリがO(d);SAGAのようなsampleごとの勾配保存が不要', 'epochごとに全勾配計算が必要;内側ループ長とstep sizeの調整;online/streamingに不向き', 'snapshot更新頻度の不適切;step size過大でdivergence;plateau', '有限和でない純粋なstreaming目的;勾配が不正;非凸学習での保証が必要な場合(出典では未確立)', 'unknown', '有限和の凸ERMでSGDの分散が収束を律速している場合。', '内側ループでloss増加;全勾配計算費が支配的;SGDと差が出ない。', 'low', 'medium', 'medium', 'medium', 'full_gradient_norm_tolerance;epoch_budget;validation_metric', 'train_loss;full_gradient_norm;learning_rate;epoch_count;seed_variance', 'M_SGD', 'MF_STOCHASTIC_ML', '', 'S113', 'medium', '2026-10-10'
),
(
  'M_SAGA', 'SAGA', 'SAGA (incremental gradient method with variance reduction)', 'SAGA', 'MF_STOCHASTIC_ML', 'variant', '各sampleの最新勾配を保存し、その平均を用いて確率的勾配を補正する分散縮小法。proximal演算子による合成目的にも対応する。', 'machine_learning;finite_sum_ERM;composite_convex', '有限和形式の目的。各項が滑らか(強凸なら線形収束、凸のみでも収束保証が示される)。合成項にはproximal演算子が必要(出典の主張範囲)。', 'stochastic_gradient;automatic_differentiation', 'continuous_high_dimensional', 'usually_unconstrained;proximal_composite_term', 'strong_theory', 'unknown', 'local', 'stochastic', 'local_numerical', '滑らかな強凸有限和で線形収束、強凸でない凸でも収束率を示す(Defazio, Bach, Lacoste-Julien 2014)。非凸の保証はこの出典では示されていない。', 'training_gradient_or_loss_not_global_certificate', 'high', 'high_per_sample_gradient_table_O_n_d_general', '1 sampleの勾配1回 + 保存済み勾配テーブルの更新。epochごとの全勾配は不要。', '安価なstochastic steps。sampleごとの勾配を保存して再利用。', 'unknown', 'unknown', 'medium', 'unknown', 'variance_reduction_for_finite_sum_sampling_noise', 'low', 'projection_or_penalty', 'yes', 'no', '全勾配の定期計算が不要;proximal(合成)目的に対応;一定step sizeで線形収束(強凸)', 'sampleごとの勾配テーブルのメモリ(一般にO(nd));大規模n・高次元dでメモリ制約が厳しい', '勾配テーブルがメモリに乗らない;step size過大でdivergence;plateau', '勾配テーブルを保持できないほど大規模なn×d;有限和でないstreaming目的;非凸学習での保証が必要な場合(出典では未確立)', 'unknown', '有限和の凸ERMでメモリに余裕があり、epochごとの全勾配計算を避けたい場合。', 'メモリ不足;loss増加;SVRGやSGDと差が出ない。', 'low', 'medium', 'medium', 'medium', 'full_gradient_norm_tolerance;epoch_budget;validation_metric', 'train_loss;full_gradient_norm;learning_rate;epoch_count;seed_variance', 'M_SGD;M_SVRG', 'MF_STOCHASTIC_ML', '', 'S114', 'medium', '2026-10-10'
);

UPDATE methods
SET child_method_ids = 'M_SGD;M_MOMENTUM_SGD;M_ADAM;M_ADAMW;M_ADAGRAD;M_RMSPROP;M_SVRG;M_SAGA'
WHERE method_id = 'MF_STOCHASTIC_ML';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_STOCHASTIC_ML_ADAGRAD', 'MF_STOCHASTIC_ML', 'M_ADAGRAD', 'is_a', 1, 'yes', 'AdaGrad is classified under Stochastic-gradient and ML optimization.', 'S112', 'medium', '2026-10-10'),
('MH_STOCHASTIC_ML_RMSPROP', 'MF_STOCHASTIC_ML', 'M_RMSPROP', 'is_a', 1, 'yes', 'RMSprop is classified under Stochastic-gradient and ML optimization.', 'S115;S116', 'medium', '2026-10-10'),
('MH_STOCHASTIC_ML_SVRG', 'MF_STOCHASTIC_ML', 'M_SVRG', 'is_a', 1, 'yes', 'Stochastic variance reduced gradient is classified under Stochastic-gradient and ML optimization.', 'S113', 'medium', '2026-10-10'),
('MH_STOCHASTIC_ML_SAGA', 'MF_STOCHASTIC_ML', 'M_SAGA', 'is_a', 1, 'yes', 'SAGA is classified under Stochastic-gradient and ML optimization.', 'S114', 'medium', '2026-10-10');

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES
('TERM_ADAGRAD', 'method', 'M_ADAGRAD', '適応的劣勾配法', 'AdaGrad', '[]',
 '["adaptive subgradient method"]', '["座標別学習率"]', '[]', '[]',
 'Adam・RMSPropとは別の手法。AdaGradは二乗勾配を累積する。', 'ja-JP,en',
 '表記ゆれ(AdaGrad/Adagrad)と正式名をmethodへ解決する。Adagradは大文字小文字違いのためlabel_enで吸収される。', '["S112"]', '2026-10-10'),
('TERM_RMSPROP', 'method', 'M_RMSPROP', 'RMSprop法', 'RMSprop', '[]',
 '[]', '["二乗勾配の移動平均"]', '[]', '[]',
 'AdaGradとは別の手法。RMSpropは二乗勾配を指数移動平均し、累積し続けない。綴りはRMSprop/RMSPropの両方が使われる。', 'ja-JP,en',
 '表記ゆれ(RMSprop/RMSProp)をmethodへ解決する。RMSPropは大文字小文字違いのためlabel_enで吸収される。', '["S115"]', '2026-10-10'),
('TERM_SVRG', 'method', 'M_SVRG', '確率的分散縮小勾配法', 'Stochastic variance reduced gradient', '["SVRG"]',
 '["分散縮小勾配法"]', '["分散縮小"]', '[]', '[]',
 'SAGAとは別の手法。SVRGはsnapshot全勾配、SAGAはsampleごとの保存勾配を制御変量にする。', 'ja-JP,en',
 '略称と正式名をmethodへ解決する。', '["S113"]', '2026-10-10'),
('TERM_SAGA', 'method', 'M_SAGA', 'SAGA法', 'SAGA', '[]',
 '["SAGA incremental gradient"]', '["分散縮小"]', '[]', '[]',
 'SVRGとは別の手法。SAGAはsampleごとの勾配を保存する。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S114"]', '2026-10-10');

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level, api_name,
  method_selector, implementation_notes, limitations, source_ids, confidence, last_verified
) VALUES
('MIM_STOCHASTIC_ML_ADAGRAD_PYTORCH', 'M_ADAGRAD', 'I_PYTORCH_OPTIM', 'native', 'torch.optim.Adagrad', '',
 'optimizer classごとにsparse gradient、foreach/fused/capturable、memoryが異なる。', '機能・status・optionはversionとbackendで確認。実装対応は一般的推奨を意味しない。', 'S048', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_ADAGRAD_OPTAX', 'M_ADAGRAD', 'I_OPTAX', 'native', 'optax.adagrad', '',
 'optimizer transformation library。training loop、schedule、regularization、state checkpointは利用者が管理。', '機能・status・optionはversionとbackendで確認。実装対応は一般的推奨を意味しない。', 'S047', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_RMSPROP_PYTORCH', 'M_RMSPROP', 'I_PYTORCH_OPTIM', 'native', 'torch.optim.RMSprop', '',
 'centered(Graves 2013)とmomentumのoptionがある。epsは平方根の後に加える規約。', '機能・status・optionはversionとbackendで確認。TensorFlowとはepsの位置が異なる。実装対応は一般的推奨を意味しない。', 'S115', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_RMSPROP_OPTAX', 'M_RMSPROP', 'I_OPTAX', 'native', 'optax.rmsprop', '',
 'optimizer transformation library。training loop、schedule、regularization、state checkpointは利用者が管理。', '機能・status・optionはversionとbackendで確認。epsの位置など数値規約は他frameworkと一致するとは限らない。実装対応は一般的推奨を意味しない。', 'S047', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_RMSPROP_KERAS', 'M_RMSPROP', 'I_TENSORFLOW_OPTIM', 'native', 'tf.keras.optimizers.RMSprop', '',
 '', '機能・status・optionはversionとbackendで確認。PyTorchとはepsの位置が異なる(PyTorch docsの記述)。実装対応は一般的推奨を意味しない。', 'S049', 'medium', '2026-10-10'),
('MIM_STOCHASTIC_ML_ADAGRAD_KERAS', 'M_ADAGRAD', 'I_TENSORFLOW_OPTIM', 'native', 'tf.keras.optimizers.Adagrad', '',
 '', '機能・status・optionはversionとbackendで確認。実装対応は一般的推奨を意味しない。', 'S049', 'medium', '2026-10-10');

UPDATE implementations SET supported_method_ids = supported_method_ids || ';M_ADAGRAD;M_RMSPROP'
WHERE implementation_id IN ('I_PYTORCH_OPTIM', 'I_OPTAX', 'I_TENSORFLOW_OPTIM');

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004194', 'S112', 'methods', 'M_ADAGRAD', 'row', '座標ごとの勾配二乗和で学習率を割る適応的step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004195', 'S047', 'methods', 'M_ADAGRAD', 'row', '座標ごとの勾配二乗和で学習率を割る適応的step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004196', 'S048', 'methods', 'M_ADAGRAD', 'row', '座標ごとの勾配二乗和で学習率を割る適応的step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004197', 'S049', 'methods', 'M_ADAGRAD', 'row', '座標ごとの勾配二乗和で学習率を割る適応的step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004198', 'S115', 'methods', 'M_RMSPROP', 'row', '二乗勾配の指数移動平均で学習率を割る座標別step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004199', 'S116', 'methods', 'M_RMSPROP', 'row', '二乗勾配の指数移動平均で学習率を割る座標別step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004200', 'S047', 'methods', 'M_RMSPROP', 'row', '二乗勾配の指数移動平均で学習率を割る座標別step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004201', 'S048', 'methods', 'M_RMSPROP', 'row', '二乗勾配の指数移動平均で学習率を割る座標別step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004202', 'S049', 'methods', 'M_RMSPROP', 'row', '二乗勾配の指数移動平均で学習率を割る座標別step調整。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004203', 'S113', 'methods', 'M_SVRG', 'row', 'snapshot点の全勾配を制御変量にして確率的勾配の分散を抑える。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004204', 'S114', 'methods', 'M_SAGA', 'row', 'sampleごとの保存勾配の平均で確率的勾配を補正する分散縮小法。', 'supporting_or_primary', 'medium', '2026-10-10');
