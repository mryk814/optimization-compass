-- Add Bellman-Ford, augmenting-path maximum flow, push-relabel and successive shortest path
-- (editorial scope TOPIC_BELLMAN_FORD / TOPIC_AUGMENTING_MAXFLOW / TOPIC_PUSH_RELABEL / TOPIC_SUCCESSIVE_SHORTEST_PATH).
-- All four are placed in MF_GRAPH_DP beside M_DIJKSTRA_ASTAR, M_NETWORK_SIMPLEX and M_HUNGARIAN: each is a dedicated algorithm that
-- exploits path / flow structure. Ford-Fulkerson and Edmonds-Karp are one row (M_AUGMENTING_MAXFLOW): Edmonds-Karp is the
-- shortest-augmenting-path rule of the Ford-Fulkerson method, so the rule is kept as an alias and in the text, not as a second row.
-- Not added: TOPIC_SUBMODULAR_GREEDY. No existing family fits without stretching its definition (MF_GRAPH_DP is path / flow / matching / DP
-- structure, MF_DISCRETE_EXACT is bound-and-gap search); it needs a decision by the maintainers, so it gets no row here.
-- No implementation rows: there is no existing implementation row for NetworkX or the OR-Tools graph solvers, and this batch adds none.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S140', 'original_paper',
  'On a routing problem',
  'Richard Bellman', '1958-01-01', '2026-10-10',
  'https://doi.org/10.1090/qam/102435',
  'Functional-equation (dynamic programming) formulation of the shortest-path routing problem on a network, solved by successive approximation.',
  'primary', 'Quarterly of Applied Mathematics 16(1), 87-90 (1958). Volume, issue and pages confirmed on 2026-10-10 against bibliographic listings (MR 102435); the AMS DOI 10.1090/qam/102435 was reported by search against the AMS listing but the DOI page itself could not be opened from this environment. L. R. Ford Jr., Network flow theory, RAND P-923 (1956), is the other origin of the method (hence the name Bellman-Ford; E. F. Moore is also credited); the RAND report was located but its content was not read, so it is not recorded as a source.',
  'historical_primary'
),
(
  'S141', 'original_paper',
  'Maximal flow through a network',
  'L. R. Ford Jr.; D. R. Fulkerson', '1956-01-01', '2026-10-10',
  'https://doi.org/10.4153/CJM-1956-045-5',
  'Max-flow min-cut theorem: the maximal flow value between two nodes equals the minimal capacity of a cut separating them; flow is built up by augmenting paths.',
  'primary', 'Canadian Journal of Mathematics 8, 399-404 (1956), DOI 10.4153/CJM-1956-045-5. Confirmed on 2026-10-10 against the Cambridge Core record via search.',
  'historical_primary'
),
(
  'S142', 'original_paper',
  'Theoretical improvements in algorithmic efficiency for network flow problems',
  'Jack Edmonds; Richard M. Karp', '1972-04-01', '2026-10-10',
  'https://doi.org/10.1145/321694.321699',
  'Augmenting-path maximum-flow rules with polynomial running time independent of the capacities (shortest augmenting path, a fattest-path variant) and a scaling method for minimum-cost flow.',
  'primary', 'Journal of the ACM 19(2), 248-264 (1972), DOI 10.1145/321694.321699. Volume, issue and pages confirmed on 2026-10-10 against the Journal of the ACM Bibliography listing via search. The full text was not read; the claim is limited to the title and the commonly cited result for the shortest-augmenting-path rule.',
  'historical_primary'
),
(
  'S143', 'original_paper',
  'A new approach to the maximum-flow problem',
  'Andrew V. Goldberg; Robert E. Tarjan', '1988-10-01', '2026-10-10',
  'https://doi.org/10.1145/48014.61051',
  'Push-relabel method based on preflows: O(n^3) time on n vertices, and O(nm log(n^2/m)) with dynamic trees on m edges.',
  'primary', 'Journal of the ACM 35(4), 921-940 (1988). Volume, issue, pages, the preflow basis and both time bounds confirmed on 2026-10-10 against the ACM author listing and the abstract via search; the DOI string was not displayed in any search result and is given from the standard ACM record. A preliminary version appeared at STOC 1986.',
  'historical_primary'
),
(
  'S144', 'textbook',
  'Network Flows: Theory, Algorithms, and Applications',
  'Ravindra K. Ahuja; Thomas L. Magnanti; James B. Orlin', '1993-01-01', '2026-10-10',
  'https://mitmgmtfaculty.mit.edu/jorlin/network-flows',
  'Textbook treatment of shortest path, maximum flow and minimum-cost flow algorithms, including label-correcting (Bellman-Ford), augmenting-path, preflow-push and successive shortest path methods.',
  'primary', 'Prentice Hall, 1993, ISBN 013617549X; the book is described on the author page as treating shortest path, maximum flow and minimum cost flow problems. Confirmed on 2026-10-10 against library and publisher catalog records via search. Busacker and Gowen (ORO Technical Paper 15, Johns Hopkins University, 1960/1961 depending on the listing) introduced successive augmentation for minimum-cost flow, but no authoritative listing or copy was found, so it is not recorded.',
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
  'M_BELLMAN_FORD', 'Bellman-Ford法', 'Bellman-Ford algorithm', 'Bellman-Ford;Bellman-Ford-Moore;label-correcting shortest path', 'MF_GRAPH_DP', 'variant', '各辺を繰り返し緩和(relax)して始点からの最短距離を更新する最短路アルゴリズム。負の辺重みを扱え、始点から到達できる負閉路を検出できる。', 'graph;shortest_path;network', '辺重み付き有向graph。負の辺重みを許すが、最短路を定義するには始点から到達できる負閉路がないこと(あれば検出して報告する)。', 'none', 'graph;discrete', 'structure_specific', 'not_applicable', 'structure_specific', 'global_certificate', 'deterministic', 'exact_with_tolerance', '頂点数n、辺数mのgraphで最大n-1回の全辺緩和により最短距離を確定でき、n回目の緩和で更新が起きれば負閉路がある(出典の標準的な結果)。計算量は一般にO(nm)。', 'algorithm_specific', 'high', 'low_to_medium', 'n回までの全辺緩和。1回あたりO(m)。', 'black-box評価ではなく辺を走査。', 'method_specific', 'not_applicable', 'low', 'low', 'not_applicable', 'native_discrete', 'structure_specific', 'conditional', 'yes_by_distributed_variant', '負の辺重みと負閉路検出を扱える;実装が単純;分散・差分的に更新しやすい', '辺重みが非負のときはDijkstra法より遅い(O(nm)対ほぼ線形対数);負閉路があると最短路が定義されない', 'negative_cycle;unreachable_nodes;large_graph_slowdown', '辺重みがすべて非負で大規模(Dijkstra法で足りる);最短路を求める始点が多数で全点対が必要', 'unknown', '辺重みに負が含まれる、または負閉路(裁定取引の循環など)の有無を調べたい最短路問題。', '負の重みが無いと分かる;大規模graphで時間が支配的;全点対が必要。', 'low_to_medium', 'low', 'low', 'high', 'algorithm_completion;no_update_in_pass', 'relaxation_passes;negative_cycle_flag;edges;updates_per_pass', 'M_DIJKSTRA_ASTAR;M_DYNAMIC_PROGRAMMING;M_SUCCESSIVE_SHORTEST_PATH', 'MF_GRAPH_DP', '', 'S140;S144', 'medium', '2026-10-10'
),
(
  'M_AUGMENTING_MAXFLOW', '増加路法(最大流)', 'Augmenting-path maximum flow (Ford-Fulkerson / Edmonds-Karp)', 'Ford-Fulkerson;Edmonds-Karp;augmenting path;augmenting path method;shortest augmenting path', 'MF_GRAPH_DP', 'variant', '残余graph上で始点から終点への増加路を見つけて流量を増やすことを、増加路が無くなるまで繰り返す最大流アルゴリズム。増加路を幅優先探索の最短路で選ぶ規則がEdmonds-Karp法。', 'graph;network;max_flow;min_cut;bipartite_matching', '容量付き有向graph、始点と終点。容量が整数(または有理数)であること。無理数容量では素朴な増加路選択が停止しないことがある。', 'none', 'graph;discrete', 'structure_specific', 'not_applicable_or_integral_polytope', 'structure_specific', 'global_certificate', 'deterministic', 'exact_with_tolerance', '終了時の流量は最小cut容量に等しい(max-flow min-cut定理)。容量が整数なら整数流が得られる。最短増加路を選ぶEdmonds-Karp規則は容量に依らない多項式回(O(nm)回)の増加で終了する。', 'min_cut', 'high', 'low_to_medium', '増加路探索1回あたりO(m)(幅優先探索)。', 'black-box評価ではなくgraphを走査。', 'method_specific', 'not_applicable', 'low', 'low', 'not_applicable', 'native_discrete', 'structure_specific', 'yes', 'yes_by_incremental_update', '最大流と同時に最小cutが得られる;整数容量で整数流;二部マッチングなどに直接使える', '増加路の選び方で計算量が大きく変わる(任意選択だと容量に比例する反復);密なgraphではpush-relabel法のほうが漸近的に有利になりうる', 'non_terminating_irrational_capacities;slow_augmentation_sequence;memory_for_residual_graph', '費用を最小化したい(最小費用流が必要);容量が無理数で素朴な増加路選択', 'unknown', '容量付きgraphの最大流・最小cut、または二部マッチングなど、費用を持たないflow問題。', '密で巨大なgraphで増加回数が支配的;費用を持つflowが必要。', 'low_to_medium', 'low', 'low', 'high', 'algorithm_completion;no_augmenting_path', 'flow_value;augmentations;min_cut_capacity;residual_edges', 'M_PUSH_RELABEL;M_SUCCESSIVE_SHORTEST_PATH;M_NETWORK_SIMPLEX;M_HUNGARIAN', 'MF_GRAPH_DP', '', 'S141;S142;S144', 'medium', '2026-10-10'
),
(
  'M_PUSH_RELABEL', 'Push-relabel法', 'Push-relabel maximum flow', 'push-relabel;preflow-push;Goldberg-Tarjan;preflow push', 'MF_GRAPH_DP', 'variant', '増加路ではなくpreflow(流入が流出を上回ってよい流れ)を保ち、超過流量を持つ頂点から高さ(label)を使って押し(push)、持ち上げる(relabel)ことで最大流を求めるアルゴリズム。', 'graph;network;max_flow;min_cut', '容量付き有向graph、始点と終点。', 'none', 'graph;discrete', 'structure_specific', 'not_applicable_or_integral_polytope', 'structure_specific', 'global_certificate', 'deterministic', 'exact_with_tolerance', 'n頂点でO(n^3)時間、動的木を使うとm辺でO(nm log(n^2/m))時間(Goldberg and Tarjan 1988)。', 'min_cut', 'very_high', 'low_to_medium', 'push/relabel操作の局所的な更新。', 'black-box評価ではなくgraphを走査。', 'high_by_local_operations', 'not_applicable', 'low', 'low', 'not_applicable', 'native_discrete', 'structure_specific', 'conditional', 'unknown', '操作が頂点に局所的で並列化しやすい;密なgraphで増加路法より漸近的に良い;実用ソルバーの基礎になる', '実装が増加路法より複雑;高さ更新の工夫(gap, global relabeling)なしでは実用で遅くなりうる', 'slow_without_heuristics;implementation_bug;memory_for_excess_and_heights', '小さなgraph(増加路法で足りる);費用を最小化したい(最小費用流が必要)', 'unknown', '大規模で密な容量付きgraphの最大流・最小cut。', '増加路法の反復が支配的;並列・GPU向けの局所操作が欲しい。', 'low', 'medium', 'high', 'medium', 'algorithm_completion;no_active_vertex', 'flow_value;active_vertices;pushes;relabels', 'M_AUGMENTING_MAXFLOW;M_NETWORK_SIMPLEX', 'MF_GRAPH_DP', '', 'S143;S144', 'medium', '2026-10-10'
),
(
  'M_SUCCESSIVE_SHORTEST_PATH', '逐次最短路法', 'Successive shortest path (min-cost flow)', 'successive shortest path;SSP;successive shortest path algorithm;Busacker-Gowen', 'MF_GRAPH_DP', 'variant', '残余graph上の最小費用の増加路(縮約費用での最短路)を繰り返し選んで流量を増やし、所定の流量に達するまで最小費用流を保ったまま構成する最小費用流アルゴリズム。', 'graph;network;min_cost_flow;assignment;transport', '容量・費用付き有向graph、供給需要。初期の残余graphに負費用閉路がないこと(あればまず除去)。容量・供給が整数。', 'none', 'graph;discrete', 'structure_specific', 'not_applicable_or_integral_polytope', 'structure_specific', 'global_certificate', 'deterministic', 'exact_with_tolerance', '各反復で縮約費用に関する最適性条件を保つため、終了時の流れは最小費用流。容量・供給が整数なら整数流が得られる。反復回数は総供給量で抑えられる擬多項式アルゴリズム(Ahuja, Magnanti, Orlin)。', 'algorithm_specific', 'medium_to_high', 'low_to_medium', '最短路計算1回(Dijkstra法またはBellman-Ford法)と電位の更新。', 'black-box評価ではなくgraphを走査。', 'method_specific', 'not_applicable', 'low', 'low_to_medium', 'not_applicable', 'native_discrete', 'structure_specific', 'conditional', 'yes_by_incremental_update', '最小費用流を直接構成し、割当て・輸送問題を解ける;縮約費用と電位で最適性を説明しやすい;流量を1単位ずつ増やす途中結果が使える', '総供給量が大きいと反復が多い(擬多項式);大規模ではnetwork simplexやscaling法が有利なことがある', 'negative_cycle_in_initial_residual;slow_for_large_supply;potential_update_bug', '供給量が非常に大きい;初期に負閉路があり除去していない', 'unknown', '費用付きflow・割当て・輸送で、供給量が小〜中程度、あるいは増分的に流量を増やしたい場合。', '総供給量が大きく反復が支配的;大規模でnetwork simplexのほうが速い。', 'medium', 'low', 'medium', 'high', 'algorithm_completion;required_flow_reached', 'flow_value;total_cost;reduced_cost_violation;augmentations', 'M_NETWORK_SIMPLEX;M_BELLMAN_FORD;M_DIJKSTRA_ASTAR;M_AUGMENTING_MAXFLOW;M_HUNGARIAN', 'MF_GRAPH_DP', '', 'S144', 'medium', '2026-10-10'
);

UPDATE methods
SET child_method_ids = 'M_DYNAMIC_PROGRAMMING;M_NETWORK_SIMPLEX;M_HUNGARIAN;M_DIJKSTRA_ASTAR;M_LOCAL_SEARCH_COMBINATORIAL;M_BELLMAN_FORD;M_AUGMENTING_MAXFLOW;M_PUSH_RELABEL;M_SUCCESSIVE_SHORTEST_PATH'
WHERE method_id = 'MF_GRAPH_DP';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_GRAPH_DP_BELLMAN_FORD', 'MF_GRAPH_DP', 'M_BELLMAN_FORD', 'is_a', 1, 'yes', 'Bellman-Ford is a shortest-path algorithm classified with Dijkstra / A* under Graph algorithms and dynamic programming.', 'S140;S144', 'medium', '2026-10-10'),
('MH_GRAPH_DP_AUGMENTING_MAXFLOW', 'MF_GRAPH_DP', 'M_AUGMENTING_MAXFLOW', 'is_a', 1, 'yes', 'Augmenting-path maximum flow is a dedicated flow algorithm classified under Graph algorithms and dynamic programming.', 'S141;S142', 'medium', '2026-10-10'),
('MH_GRAPH_DP_PUSH_RELABEL', 'MF_GRAPH_DP', 'M_PUSH_RELABEL', 'is_a', 1, 'yes', 'Push-relabel is a dedicated maximum-flow algorithm classified with the augmenting-path method under Graph algorithms and dynamic programming.', 'S143;S144', 'medium', '2026-10-10'),
('MH_GRAPH_DP_SUCCESSIVE_SHORTEST_PATH', 'MF_GRAPH_DP', 'M_SUCCESSIVE_SHORTEST_PATH', 'is_a', 1, 'yes', 'Successive shortest path is a dedicated minimum-cost-flow algorithm classified with network simplex under Graph algorithms and dynamic programming.', 'S144;S142', 'medium', '2026-10-10');

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES
('TERM_BELLMAN_FORD', 'method', 'M_BELLMAN_FORD', 'Bellman-Ford法', 'Bellman-Ford algorithm', '[]',
 '["Bellman-Ford-Moore","label-correcting shortest path"]', '["負閉路検出","辺の緩和"]', '[]', '[]',
 '非負の辺重みを前提とするDijkstra法とは別の手法。Bellman方程式による動的計画法の一般形とも別。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S140"]', '2026-10-10'),
('TERM_AUGMENTING_MAXFLOW', 'method', 'M_AUGMENTING_MAXFLOW', '増加路法', 'Ford-Fulkerson method', '[]',
 '["Edmonds-Karp","augmenting path method","最大流アルゴリズム"]', '["残余graph","max-flow min-cut"]', '[]', '[]',
 'Edmonds-Karp法はFord-Fulkerson法の増加路を最短路で選ぶ規則で、同じ行に収める。push-relabel法は別のmethod。', 'ja-JP,en',
 '名称と規則名をmethodへ解決する。', '["S141","S142"]', '2026-10-10'),
('TERM_PUSH_RELABEL', 'method', 'M_PUSH_RELABEL', 'Push-relabel法', 'Push-relabel algorithm', '[]',
 '["preflow-push","Goldberg-Tarjan algorithm"]', '["preflow","超過流量"]', '[]', '[]',
 '増加路法(Ford-Fulkerson / Edmonds-Karp)とは別の最大流アルゴリズム。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S143"]', '2026-10-10'),
('TERM_SUCCESSIVE_SHORTEST_PATH', 'method', 'M_SUCCESSIVE_SHORTEST_PATH', '逐次最短路法', 'Successive shortest path algorithm', '["SSP"]',
 '["Busacker-Gowen algorithm","最小費用流の増加路法"]', '["縮約費用","電位"]', '[]', '[]',
 '最大流の増加路法(費用なし)やnetwork simplexとは別の最小費用流アルゴリズム。', 'ja-JP,en',
 '略称と名称をmethodへ解決する。', '["S144"]', '2026-10-10');

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004249', 'S140', 'methods', 'M_BELLMAN_FORD', 'row', '辺の緩和を繰り返して最短路を求め、負の辺重みを扱う。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004250', 'S144', 'methods', 'M_BELLMAN_FORD', 'row', '辺の緩和を繰り返して最短路を求め、負の辺重みを扱う。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004251', 'S141', 'methods', 'M_AUGMENTING_MAXFLOW', 'row', '残余graphの増加路で流量を増やし、最大流と最小cutを得る。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004252', 'S142', 'methods', 'M_AUGMENTING_MAXFLOW', 'row', '残余graphの増加路で流量を増やし、最大流と最小cutを得る。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004253', 'S143', 'methods', 'M_PUSH_RELABEL', 'row', 'preflowを保ちpushとrelabelで最大流を求める。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004254', 'S144', 'methods', 'M_PUSH_RELABEL', 'row', 'preflowを保ちpushとrelabelで最大流を求める。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004255', 'S144', 'methods', 'M_SUCCESSIVE_SHORTEST_PATH', 'row', '残余graphの最短路で流量を増やし最小費用流を構成する。', 'supporting_or_primary', 'medium', '2026-10-10');
