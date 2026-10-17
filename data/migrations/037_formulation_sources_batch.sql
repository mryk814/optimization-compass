-- Add primary sources for formulation articles that had no source stating their core claims.
-- A source audit on 2026-10-14 mapped each remaining problem archetype's core claims to existing sources. Only
-- PA049 was covered; PA002, PA003, PA022, PA027, PA030, PA044, PA047, PA050, PA051, PA052, PA053, PA054 and PA056
-- had existing sources whose supported_claim was too coarse (for example "problem classes" or "ADMM") or off topic.
-- This batch records one or two primary sources per gap and links them to the archetype rows.
-- Source-only batch: no method, implementation, problem or vocabulary rows, and no change to problem_method_fit.
-- Bibliographic data (title, authors, year, venue, volume/issue/pages, DOI) was confirmed against the Crossref REST
-- API on 2026-10-14. Abstracts were read where Crossref or the publisher page provided them; for the others the
-- supported_claim states the book's or paper's known scope and the evidence link confidence is medium, as each
-- source's notes say. Full texts were not read.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S173', 'textbook',
  'Numerical Linear Algebra',
  'Lloyd N. Trefethen; David Bau, III', '1997-01-01', '2026-10-14',
  'https://doi.org/10.1137/1.9780898719574',
  'Textbook treatment of numerical linear algebra: the singular value decomposition and low-rank approximation, QR factorization and least squares, conditioning and stability, Gaussian elimination (LU) and Cholesky factorization for linear systems, eigenvalue algorithms including the Rayleigh quotient and QR iteration, and Krylov subspace iterations including Arnoldi, Lanczos and conjugate gradients.',
  'primary', 'SIAM, 1997, ISBN 978-0-89871-361-9 (print), 978-0-89871-957-4 (ebook). DOI 10.1137/1.9780898719574. Crossref REST API (api.crossref.org/works/10.1137/1.9780898719574) checked 2026-10-14: title, authors, year, publisher, ISBNs. SIAM page returned 403, so no publisher description was read; the claim is limited to the well-known lecture structure (SVD, QR, eigenvalue problems) - confirm against the TOC before final use. Covers SVD low-rank approximation and Rayleigh quotient/eigenvalue algorithms. Alternative: Golub & Van Loan, Matrix Computations 4th ed. (not verified; JHU Press DOI not checked).',
  'historical_primary'
),
(
  'S174', 'textbook',
  'Lectures on Modern Convex Optimization',
  'Aharon Ben-Tal; Arkadi Nemirovski', '2001-01-01', '2026-10-14',
  'https://doi.org/10.1137/1.9780898718829',
  'Monograph on conic optimization (linear, conic quadratic and semidefinite programming), their duality theory, interior-point algorithms, and engineering applications including robust optimization.',
  'primary', 'SIAM / MPS-SIAM Series on Optimization, 2001, ISBN 978-0-89871-491-3 (Crossref lists 9780898714913 and 9780898718829). DOI 10.1137/1.9780898718829. Crossref REST API (api.crossref.org/works/10.1137/1.9780898718829) checked 2026-10-14: title, authors, year, publisher, ISBNs. Crossref title has no subtitle (the usual subtitle ''Analysis, Algorithms, and Engineering Applications'' is unconfirmed, so omitted). No publisher description read (403). Claim is from the known scope of the book, not a read description.',
  'historical_primary'
),
(
  'S175', 'original_paper',
  'Conic Optimization via Operator Splitting and Homogeneous Self-Dual Embedding',
  'Brendan O''Donoghue; Eric Chu; Neal Parikh; Stephen Boyd', '2016-02-22', '2026-10-14',
  'https://doi.org/10.1007/s10957-016-0892-3',
  'Method for solving convex cone programs by applying operator splitting (ADMM) to the homogeneous self-dual embedding, which also yields certificates of infeasibility or unboundedness (the algorithm behind SCS).',
  'primary', 'Journal of Optimization Theory and Applications 169(3), 1042-1068 (2016). DOI 10.1007/s10957-016-0892-3. Crossref REST API (api.crossref.org/works/10.1007/s10957-016-0892-3) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages. Online date 2016-02-22, print issue June 2016. Abstract not in Crossref; claim restricted to title-level statement plus the known abstract point (infeasibility/unboundedness certificates) - confirm. Primary reference for SCS (S013).',
  'historical_primary'
),
(
  'S176', 'textbook',
  'Handbook of Satisfiability (Second Edition)',
  'Armin Biere; Marijn Heule; Hans van Maaren; Toby Walsh (editors)', '2021-02-02', '2026-10-14',
  'https://doi.org/10.3233/FAIA336',
  'Edited handbook covering SAT theory and practice: search algorithms including conflict-driven clause learning, encodings, proof complexity, hard instances, and solvers; the second edition adds a core-based MaxSAT chapter per its preface.',
  'primary', 'IOS Press, Frontiers in Artificial Intelligence and Applications 336, 2021, ISBN 978-1-64368-160-3. DOI 10.3233/FAIA336. Crossref REST API (api.crossref.org/works/10.3233/FAIA336) checked 2026-10-14: title, authors, year, publisher, editors/ISBN; publisher page ebooks.iospress.nl/volume/handbook-of-satisfiability-second-edition read via WebFetch (description, editors, chapter list: Ch.4 Conflict-Driven Clause Learning SAT Solvers by Marques-Silva, Lynce, Malik; proof complexity chapters; the preface mentions a new core-based MaxSAT chapter but its title was not visible). Authors are editors; cite chapter-level (Ch.4 for CDCL). Optional extra for NP-completeness of SAT: Cook 1971, STOC ''71 pp.151-158, DOI 10.1145/800157.805047 (Crossref-verified).',
  'historical_primary'
),
(
  'S177', 'original_paper',
  'The Hungarian method for the assignment problem',
  'H. W. Kuhn', '1955-03-01', '2026-10-14',
  'https://doi.org/10.1002/nav.3800020109',
  'Given numerical scores for n persons on n jobs, the assignment problem seeks an assignment maximizing the total score; the paper exploits ideas of two Hungarian mathematicians to give a new solution method.',
  'primary', 'Naval Research Logistics Quarterly 2(1-2), 83-97 (1955). DOI 10.1002/nav.3800020109. Crossref REST API (api.crossref.org/works/10.1002/nav.3800020109) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages; abstract read from Crossref. Original Hungarian method. Integrality of the LP relaxation is not in the abstract; do not cite this source for it.',
  'historical_primary'
),
(
  'S178', 'original_paper',
  'Survey of Numerical Methods for Trajectory Optimization',
  'John T. Betts', '1998-03-01', '2026-10-14',
  'https://doi.org/10.2514/2.4231',
  'Survey of numerical methods for trajectory optimization, i.e., optimal control problems solved by indirect and direct (transcription to nonlinear programming) approaches.',
  'primary', 'Journal of Guidance, Control, and Dynamics 21(2), 193-207 (1998). DOI 10.2514/2.4231. Crossref REST API (api.crossref.org/works/10.2514/2.4231) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages. Abstract not retrieved; claim limited to title-level statement. Standard survey for direct vs indirect trajectory optimization; complements S102, S042, S043.',
  'historical_primary'
),
(
  'S179', 'textbook',
  'Finite-Dimensional Variational Inequalities and Complementarity Problems',
  'Francisco Facchinei; Jong-Shi Pang', '2004-01-01', '2026-10-14',
  'https://doi.org/10.1007/b97543',
  'Monograph on finite-dimensional variational inequalities and complementarity problems: formulation, existence and uniqueness of solutions, and applications to equilibrium problems (volume I); algorithms are in volume II (DOI 10.1007/b97544, not checked).',
  'primary', 'Springer Series in Operations Research and Financial Engineering, Springer, Volume I, ISBN 978-0-387-95580-3. DOI 10.1007/b97543. Crossref REST API (api.crossref.org/works/10.1007/b97543) checked 2026-10-14: title, authors, year, publisher, ISBN. Crossref issued year is 2004 (volume I print copyright is commonly 2003 - unconfirmed) and its authors appear as an editors field. Springer page redirected to login; no description read. Claim limited to title-level scope. Add volume II if algorithms are cited.',
  'historical_primary'
),
(
  'S180', 'textbook',
  'Robust Optimization',
  'Aharon Ben-Tal; Laurent El Ghaoui; Arkadi Nemirovski', '2009-08-30', '2026-10-14',
  'https://doi.org/10.1515/9781400831050',
  'Monograph on robust optimization: uncertain linear programs and their robust counterparts, the relation between uncertainty sets and chance-constrained approaches, uncertain conic quadratic and semidefinite problems, and multistage (adjustable) problems.',
  'primary', 'Princeton University Press, Princeton Series in Applied Mathematics, 2009, ISBN 978-0-691-14368-2. DOI 10.1515/9781400831050. Crossref REST API (api.crossref.org/works/10.1515/9781400831050) checked 2026-10-14: title, authors, year, publisher, ISBN (Crossref issued 2009-12-31 is the e-book date); publisher description read at press.princeton.edu (uncertain LP first, relation of uncertainty sets to chance constraints, uncertain conic quadratic and semidefinite problems, multistage problems; published August 30, 2009). Primary book for PA050. Optional: Bertsimas & Sim 2004, Oper. Res. 52(1), 35-53, DOI 10.1287/opre.1030.0065 (not Crossref-checked).',
  'historical_primary'
),
(
  'S181', 'original_paper',
  'Distributed Subgradient Methods for Multi-Agent Optimization',
  'Angelia Nedic; Asuman Ozdaglar', '2009-01-01', '2026-10-14',
  'https://doi.org/10.1109/TAC.2008.2009515',
  'Distributed subgradient method in which agents minimize the sum of their local convex objectives by combining local subgradient steps with averaging over a network, with convergence analysis.',
  'primary', 'IEEE Transactions on Automatic Control 54(1), 48-61 (2009). DOI 10.1109/TAC.2008.2009515. Crossref REST API (api.crossref.org/works/10.1109/TAC.2008.2009515) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages. Abstract not retrieved; claim limited to title-level statement. Covers decentralized (no central coordinator) consensus; complements S061 ADMM.',
  'historical_primary'
),
(
  'S182', 'original_paper',
  'Introduction to Online Convex Optimization',
  'Elad Hazan', '2016-08-30', '2026-10-14',
  'https://doi.org/10.1561/2400000013',
  'Monograph presenting optimization as a process in which a method learns as it goes, i.e., online convex optimization, for settings where a comprehensive model is infeasible.',
  'primary', 'Foundations and Trends in Optimization 2(3-4), 157-325 (2016). DOI 10.1561/2400000013. Crossref REST API (api.crossref.org/works/10.1561/2400000013) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages; abstract read from Crossref (optimization as a process; learning from experience as more of the problem is observed). Regret/OGD content is from the monograph''s known scope, not the abstract. Abstract does not mention regret explicitly; verify the TOC (regret, OGD, FTRL) before final use. Zinkevich 2003 (ICML) not DOI-verified.',
  'historical_primary'
),
(
  'S183', 'original_paper',
  'The explicit linear quadratic regulator for constrained systems',
  'Alberto Bemporad; Manfred Morari; Vivek Dua; Efstratios N. Pistikopoulos', '2002-01-01', '2026-10-14',
  'https://doi.org/10.1016/S0005-1098(01)00174-1',
  'Shows that the constrained linear quadratic regulator, a quadratic program parametrized by the state, has a piecewise affine solution on a polyhedral partition of the parameter space (explicit MPC via multiparametric programming).',
  'primary', 'Automatica 38(1), 3-20 (2002). DOI 10.1016/S0005-1098(01)00174-1. Crossref REST API (api.crossref.org/works/10.1016/S0005-1098(01)00174-1) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages. Abstract not retrieved; claim limited to title-level and well-known result (multiparametric QP gives piecewise affine control law). Check abstract on publisher page before final use.',
  'historical_primary'
),
(
  'S184', 'textbook',
  'Optimal Design of Experiments',
  'Friedrich Pukelsheim', '2006-01-01', '2026-10-14',
  'https://doi.org/10.1137/1.9780898719109',
  'Monograph on optimal design of experiments: information matrices, optimality criteria such as D-optimality, approximate designs, and the general equivalence theorem.',
  'primary', 'SIAM Classics in Applied Mathematics, 2006, ISBN 978-0-89871-604-7 (Crossref lists 9780898716047 and 9780898719109). DOI 10.1137/1.9780898719109. Crossref REST API (api.crossref.org/works/10.1137/1.9780898719109) checked 2026-10-14: title, authors, year, publisher, ISBNs. SIAM page returned 403; no description read. Claim limited to title-level scope and known contents (information matrices, D-optimality, equivalence theorem). Optional original: Kiefer & Wolfowitz 1960, Canad. J. Math. 12, 363-366, DOI 10.4153/CJM-1960-030-4 (not checked).',
  'historical_primary'
),
(
  'S185', 'original_paper',
  'Robust Estimation of a Location Parameter',
  'Peter J. Huber', '1964-03-01', '2026-10-14',
  'https://doi.org/10.1214/aoms/1177703732',
  'Introduces robust M-estimation of a location parameter under contamination of the error distribution, including the minimax (Huber) loss.',
  'primary', 'The Annals of Mathematical Statistics 35(1), 73-101 (1964). DOI 10.1214/aoms/1177703732. Crossref REST API (api.crossref.org/works/10.1214/aoms/1177703732) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages. Abstract not retrieved; claim limited to title-level topic (robust M-estimation). Foundation of the Huber loss offered in S003/S041.',
  'historical_primary'
),
(
  'S186', 'original_paper',
  'Random sample consensus',
  'Martin A. Fischler; Robert C. Bolles', '1981-06-01', '2026-10-14',
  'https://doi.org/10.1145/358669.358692',
  'RANSAC: a paradigm for fitting a model to experimental data that can interpret and smooth data containing a significant percentage of gross errors.',
  'primary', 'Communications of the ACM 24(6), 381-395 (1981). DOI 10.1145/358669.358692. Crossref REST API (api.crossref.org/works/10.1145/358669.358692) checked 2026-10-14: title, authors, year, publisher, volume/issue/pages; abstract read from Crossref. Full title has the subtitle ''a paradigm for model fitting with applications to image analysis and automated cartography'' (from memory, Crossref gives only the short form). Use Crossref title.',
  'historical_primary'
);

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004296', 'S173', 'problem_archetypes', 'PA003', 'row', '対称行列の二次形式の最小化は最小固有値の固有ベクトルで与えられ、SVDによる低ランク近似や固有値解法を標準教科書が体系的に扱っています。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004297', 'S173', 'problem_archetypes', 'PA002', 'row', '連立一次方程式を LU・Cholesky 分解や共役勾配法で解く方法と、条件数による誤差の増え方を扱う標準的な教科書です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004298', 'S174', 'problem_archetypes', 'PA022', 'row', '線形・二次錐・半正定値計画を含む錐最適化の標準形、双対理論、内点法を体系的に扱う専門書です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004299', 'S174', 'problem_archetypes', 'PA050', 'row', '不確かな錐計画のrobust対応を含む錐最適化の理論的基盤を与えます。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004300', 'S175', 'problem_archetypes', 'PA022', 'row', '一般の凸錐計画を、自己双対埋め込みへの演算子分割（ADMM）で解く一次法の原論文です。', 'supporting_or_primary', 'high', '2026-10-14'),
('EL004301', 'S176', 'problem_archetypes', 'PA027', 'row', 'SATの探索アルゴリズム（CDCL）・符号化・MaxSATを含む標準的なハンドブックです。', 'supporting_or_primary', 'high', '2026-10-14'),
('EL004302', 'S177', 'problem_archetypes', 'PA030', 'row', '割当問題（人と仕事の一対一対応で総得点を最大化）を解くハンガリー法の原論文です。', 'supporting_or_primary', 'high', '2026-10-14'),
('EL004303', 'S178', 'problem_archetypes', 'PA044', 'row', '軌道最適化を直接法・間接法に分けて整理した標準的なサーベイ論文です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004304', 'S179', 'problem_archetypes', 'PA047', 'row', '変分不等式・相補性問題の定式化と解の存在・一意性を扱う標準的な専門書です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004305', 'S180', 'problem_archetypes', 'PA050', 'row', '不確実な線形・錐計画のrobust対応問題と不確実集合の選び方を体系的に扱う標準的な専門書です。', 'supporting_or_primary', 'high', '2026-10-14'),
('EL004306', 'S181', 'problem_archetypes', 'PA051', 'row', '中央の調整役なしにネットワーク上で各主体の目的の和を最小化する分散劣勾配法の原論文です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004307', 'S182', 'problem_archetypes', 'PA052', 'row', '目的が毎回変わる状況での逐次最適化（online convex optimization）とregretを体系的に扱う標準的な専門書です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004308', 'S183', 'problem_archetypes', 'PA053', 'row', 'parameterを含む二次計画の解がparameterの区分アフィン関数になることを示した、explicit MPCの基礎論文です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004309', 'S184', 'problem_archetypes', 'PA054', 'row', '情報行列の基準（D最適など）と等価定理に基づく実験計画の最適化を体系的に扱う標準的な専門書です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004310', 'S185', 'problem_archetypes', 'PA056', 'row', '外れ値を含む観測に強いM推定とHuber損失を導入した原論文です。', 'supporting_or_primary', 'medium', '2026-10-14'),
('EL004311', 'S186', 'problem_archetypes', 'PA056', 'row', '大きな割合の誤差を含むデータにもモデルを当てはめられるRANSACの原論文です。', 'supporting_or_primary', 'high', '2026-10-14');
