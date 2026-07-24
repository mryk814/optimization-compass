const DOMAIN_LABELS: Record<string, string> = {
  agriculture: "農業・農地",
  all: "すべて",
  business: "事業・施策",
  control: "制御",
  energy: "エネルギー",
  engineering: "設計・工学",
  environment: "環境・保全",
  finance: "金融",
  healthcare: "医療・地域保健",
  logistics: "物流",
  "machine-learning": "機械学習",
  manufacturing: "製造",
  operations: "運用・計画",
  "public-policy": "公共政策",
  science: "科学・推定",
};

export function domainLabel(domain: string): string {
  return DOMAIN_LABELS[domain] ?? domain;
}
