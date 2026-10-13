-- Add primary sources for the bilevel (PA046) and complementarity (PA048) problem archetypes.
-- Before this migration both archetypes were linked only to S054 (NEOS Guide: Optimization Problem Types), which does not mention bilevel
-- optimization, MPEC, complementarity problems or Lemke's method, and PA048 also to S056 (Nocedal and Wright), which covers KKT
-- complementary slackness but not linear complementarity theory. Formulation articles for PA046 and PA048 could not state their core
-- claims (optimistic versus pessimistic bilevel solutions, the role of a unique lower-level solution, the KKT/MPCC reformulation,
-- P-matrix uniqueness and Lemke's method) with a primary source, so this batch records five.
-- Source-only batch: no new method, implementation, problem or vocabulary rows, and no change to problem_method_fit.
-- Bibliographic data was confirmed on 2026-10-13 against publisher listings, Crossref, RePEc/IDEAS and library catalog records as noted
-- per row; full texts were not read, so supported_claim is limited to what the abstracts, prefaces and tables of contents state.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S168', 'original_paper',
  'An overview of bilevel optimization',
  'Benoit Colson; Patrice Marcotte; Gilles Savard', '2007-09-01', '2026-10-13',
  'https://doi.org/10.1007/s10479-007-0176-2',
  'Survey of bilevel optimization: a leader problem constrained by the optimal response of a follower problem, its general formulation, fields of application, solution approaches, and the connection between bilevel problems and mathematical programs with equilibrium constraints (MPEC).',
  'primary', 'Annals of Operations Research 153(1), 235-256 (September 2007), Springer, DOI 10.1007/s10479-007-0176-2. Journal, volume, issue, pages, date and DOI confirmed on 2026-10-13 against the RePEc/IDEAS record; the scope in supported_claim follows the abstract indexed there. Not to be confused with the same authors'' 2005 survey in 4OR 3(2), DOI 10.1007/s10288-005-0071-0, which is not recorded.',
  'historical_primary'
),
(
  'S169', 'textbook',
  'Foundations of Bilevel Programming',
  'Stephan Dempe', '2002-05-01', '2026-10-13',
  'https://doi.org/10.1007/b101970',
  'Monograph on bilevel programming: when the lower-level problem has a unique optimal solution for every parameter the problem reduces to a one-level problem with an implicitly defined objective; when the lower-level solution is not unique, the optimistic (weak) and pessimistic (strong) approaches are distinguished; linear bilevel problems, optimality conditions, solution algorithms and discrete bilevel problems.',
  'primary', 'Kluwer Academic Publishers (now Springer), Nonconvex Optimization and Its Applications 61, 2002, ISBN 978-1-4020-0631-9 (hardback), 978-0-306-48045-4 (electronic), DOI 10.1007/b101970. Publisher, series, volume, ISBNs and DOI confirmed on 2026-10-13 against the Springer DOI listing and library catalog records; supported_claim follows the publisher description and the catalog table of contents.',
  'historical_primary'
),
(
  'S170', 'textbook',
  'Mathematical Programs with Equilibrium Constraints',
  'Zhi-Quan Luo; Jong-Shi Pang; Daniel Ralph', '1996-11-13', '2026-10-13',
  'https://doi.org/10.1017/CBO9780511983658',
  'Monograph on mathematical programs with equilibrium constraints (MPEC): constrained optimization problems whose core constraints are a parametric variational inequality or complementarity system, including bilevel programs whose lower level is replaced by its optimality conditions; exact penalization, first- and second-order optimality conditions, and algorithms.',
  'primary', 'Cambridge University Press, 1996, ISBN 978-0-521-57290-3 (hardback), online 2011, DOI 10.1017/CBO9780511983658. Publisher, year, ISBN and DOI confirmed on 2026-10-13 against Cambridge Core and library catalog records; supported_claim follows the preface on Cambridge Core and the published chapter list.',
  'historical_primary'
),
(
  'S171', 'textbook',
  'The Linear Complementarity Problem',
  'Richard W. Cottle; Jong-Shi Pang; Richard E. Stone', '2009-01-01', '2026-10-13',
  'https://doi.org/10.1137/1.9780898719000',
  'Textbook on the linear complementarity problem (LCP): find z >= 0 with w = q + Mz >= 0 and z^T w = 0; existence and multiplicity of solutions in terms of matrix classes (including P-matrices, for which the LCP has a unique solution for every q), pivoting methods including Lemke''s method, iterative methods, geometry and degree theory, and sensitivity analysis.',
  'primary', 'SIAM Classics in Applied Mathematics 60, 2009 (originally Academic Press, Boston, 1992), ISBN 978-0-89871-686-3 (print), 978-0-89871-900-0 (electronic), DOI 10.1137/1.9780898719000. Authors, publisher, ISBNs and DOI confirmed on 2026-10-13 against the Crossref record; series, volume and original edition confirmed against a library catalog record; chapter titles from a bookseller listing. Page-level claims are not recorded.',
  'historical_primary'
),
(
  'S172', 'original_paper',
  'Bimatrix equilibrium points and mathematical programming',
  'C. E. Lemke', '1965-05-01', '2026-10-13',
  'https://doi.org/10.1287/mnsc.11.7.681',
  'Constructive method for the linear complementarity system covering quadratic programming and equilibrium points of bimatrix games: it follows a path of adjacent extreme points to a solution under a non-degeneracy assumption, without reducing an objective function along the way (Lemke''s method).',
  'primary', 'Management Science 11(7), 681-689 (May 1965), INFORMS, DOI 10.1287/mnsc.11.7.681. Journal, volume, issue, pages, month and DOI confirmed on 2026-10-13 against the RePEc/IDEAS record; supported_claim follows the abstract indexed there. The 1964 Lemke and Howson SIAM paper is a separate publication and is not recorded.',
  'historical_primary'
);

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004290', 'S168', 'problem_archetypes', 'PA046', 'row', '上位問題の制約に下位問題の最適解が入る二段の問題。下位問題を最適性条件で置き換えるとMPECにつながる。', 'supporting_or_primary', 'high', '2026-10-13'),
('EL004291', 'S169', 'problem_archetypes', 'PA046', 'row', '下位問題の解が一つに決まるなら一段の問題に帰着し、決まらないなら楽観的・悲観的の二つの解き方を区別する。', 'supporting_or_primary', 'high', '2026-10-13'),
('EL004292', 'S170', 'problem_archetypes', 'PA046', 'row', '下位問題を相補性条件や変分不等式で表すと、平衡制約付き数理計画（MPEC）になる。', 'supporting_or_primary', 'medium', '2026-10-13'),
('EL004293', 'S171', 'problem_archetypes', 'PA048', 'row', '線形相補性問題 z≥0, w=q+Mz≥0, zᵀw=0 の解の存在と一意性（P行列）、Lemke法などの解法。', 'supporting_or_primary', 'high', '2026-10-13'),
('EL004294', 'S172', 'problem_archetypes', 'PA048', 'row', '線形相補性系を、隣り合う端点をたどる道筋で解く構成的な方法（Lemke法）。非退化を仮定する。', 'supporting_or_primary', 'high', '2026-10-13'),
('EL004295', 'S170', 'problem_archetypes', 'PA048', 'row', '相補性系を制約に持つ最適化（MPEC）。相補性問題の拡張として扱う。', 'supporting_or_primary', 'medium', '2026-10-13');
