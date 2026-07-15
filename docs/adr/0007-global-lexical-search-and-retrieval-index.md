# ADR 0007: Global search is lexical-first and shares a retrieval authority

- Status: accepted
- Date: 2026-07-16
- Issue: #75

## Context

Atlasの用語検索はterminology aliasだけを対象にしており、問題、手法、実装、教材、
Gallery、可視化、比較、根拠を横断できませんでした。意味検索やRAGを先に導入すると、
検索理由、更新単位、source authorityが不透明なまま別のknowledge layerが生まれます。

## Decision

build時にcanonical dataから `search-index.json` を決定的に生成します。NFKC、casefold、
句読点の空白化、日本語character bigramを共通規則とし、正式名、alias、title、要約、
keyword、関連語をfield-weightedに順位付けします。各結果は一致field、entity type、intent、
確認日、source IDを表示し、queryとfilterはURL stateに保持します。

同じdocument集合から `retrieval-documents.json` も生成します。chunk ID、document ID、
source ID、dataset version、license、attribution、authorityを必須にし、教材はh2単位、
他entityはoverview単位で分割します。frameごとのchunkは作りません。UIと将来のRAGは同じ
canonical exportを参照し、別indexを手編集しません。

## Semantic retrieval adoption gate

現時点ではembedding、vector database、AI chatを採用しません。代表query benchmarkで
lexical検索のTop-3 relevanceが継続的に不足し、語彙追加では解けない意図差が再現される
場合だけsemantic rerankを検討します。採用時は以下を必須とします。

- vector manifestにmodel名・revision、次元、distance、chunking version、dataset hashを記録する
- lexical結果を残したhybrid retrievalとし、sourceとmatch provenanceを表示する
- index size、p95 latency、recall改善、privacy/costを同じbenchmarkで比較する
- queryやclick履歴はdefaultで保存しない。保存する場合は明示同意とretention policyを設ける

## Quality and budget

`data/seeds/search_benchmark.json` はcanonical、alias、日英混在、自然文、実装、比較、根拠、
zero-resultを含みます。CIはartifactの決定性、dangling relation/source、contract、Top-1/Top-3、
期待entity到達を検証します。browser配信するlexical indexは2 MiBを暫定上限とし、
`scripts/search_benchmark.py` でbytesとlatencyを計測します。

## Consequences

検索対象の追加はentity linkまたはcanonical artifactの追加で行い、UIだけの候補一覧を増やしません。
検索schemaの変更はPython/TypeScript parserとmanifestを同期してversionを上げます。
