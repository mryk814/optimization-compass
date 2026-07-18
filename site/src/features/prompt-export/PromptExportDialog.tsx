import { useEffect, useMemo, useRef, useState } from "react";

import {
  REQUESTED_OUTPUT_OPTIONS,
  createImplementationPromptPack,
  renderImplementationPromptMarkdown,
  unknownsForForm,
  type ImplementationPromptDraft,
  type PromptFormState,
  type RequestedOutputId,
} from "./implementation-prompt";

interface PromptExportDialogProps {
  draft: ImplementationPromptDraft;
  onClose(): void;
}

type TextField = Exclude<keyof PromptFormState, "requested_outputs">;

const TEXT_FIELDS: Array<{
  field: TextField;
  label: string;
  multiline?: boolean;
}> = [
  { field: "intent", label: "やりたいこと", multiline: true },
  { field: "decision_variables", label: "決定変数 (Decision variables)", multiline: true },
  { field: "objective", label: "目的関数・最小化/最大化 (Objective)", multiline: true },
  { field: "constraints", label: "制約 (Constraints)", multiline: true },
  { field: "input_data_format", label: "入力データ・形式 (Input data / format)", multiline: true },
  { field: "problem_scale", label: "問題の規模 (Problem scale)" },
  { field: "evaluation_cost", label: "評価コスト (Evaluation cost)" },
  { field: "computation_budget", label: "計算予算 (Computation budget)" },
  { field: "programming_language", label: "プログラミング言語 (Programming language)" },
  { field: "preferred_libraries", label: "使用したいライブラリ (Preferred libraries)" },
  { field: "prohibited_libraries", label: "使用できないライブラリ (Prohibited libraries)" },
  { field: "runtime_environment", label: "実行・配備環境 (Runtime / deployment)" },
  { field: "additional_unknowns", label: "その他の不明点（1行1件）", multiline: true },
];

export function PromptExportDialog({ draft, onClose }: PromptExportDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const firstFieldRef = useRef<HTMLTextAreaElement>(null);
  const [form, setForm] = useState<PromptFormState>(() => structuredClone(draft.initial_form));
  const [markdown, setMarkdown] = useState(() =>
    renderImplementationPromptMarkdown(createImplementationPromptPack(draft, draft.initial_form)));
  const [customized, setCustomized] = useState(false);
  const [stale, setStale] = useState(false);
  const [copyStatus, setCopyStatus] = useState("");
  const unknowns = useMemo(() => unknownsForForm(form), [form]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    dialog.showModal();
    firstFieldRef.current?.focus({ preventScroll: true });
    return () => {
      if (dialog.open) dialog.close();
    };
  }, []);

  const updateForm = (next: PromptFormState) => {
    setForm(next);
    setCopyStatus("");
    if (customized) {
      setStale(true);
      return;
    }
    setMarkdown(renderImplementationPromptMarkdown(createImplementationPromptPack(draft, next)));
    setStale(false);
  };

  const updateText = (field: TextField, value: string) => {
    updateForm({ ...form, [field]: value });
  };

  const updateRequestedOutput = (id: RequestedOutputId, checked: boolean) => {
    const requested = checked
      ? [...form.requested_outputs, id]
      : form.requested_outputs.filter((item) => item !== id);
    updateForm({ ...form, requested_outputs: requested });
  };

  const regenerate = () => {
    setMarkdown(renderImplementationPromptMarkdown(createImplementationPromptPack(draft, form)));
    setCustomized(false);
    setStale(false);
    setCopyStatus("入力内容からMarkdownを再生成しました。");
  };

  const copy = async () => {
    try {
      if (!navigator.clipboard) throw new Error("クリップボードを利用できません。");
      await navigator.clipboard.writeText(markdown);
      setCopyStatus("実装用プロンプトをコピーしました。");
    } catch (caught) {
      const detail = caught instanceof Error ? caught.message : String(caught);
      setCopyStatus(`コピーできませんでした。${detail}`);
    }
  };

  return (
    <dialog
      aria-labelledby="prompt-export-title"
      className="prompt-export-dialog"
      onClose={onClose}
      ref={dialogRef}
    >
      <div className="prompt-export-shell">
        <header className="prompt-export-header">
          <div>
            <p className="eyebrow">実装用プロンプトパック</p>
            <h2 id="prompt-export-title">実装用プロンプトを作る</h2>
          </div>
          <button aria-label="実装用プロンプトを閉じる" onClick={() => dialogRef.current?.close()} type="button">閉じる</button>
        </header>
        <p className="prompt-export-privacy" role="note">
          入力はこの画面のメモリ内だけで扱い、保存・送信しません。機密情報、個人情報、秘密鍵は入力しないでください。
        </p>
        <div className="prompt-export-layout">
          <form className="prompt-export-form" onSubmit={(event) => event.preventDefault()}>
            <h3>問題ブリーフ</h3>
            <p>不明な項目は <code>unknown</code> のままで構いません。</p>
            <div className="prompt-export-fields">
              {TEXT_FIELDS.map(({ field, label, multiline }, index) => (
                <label className={multiline ? "prompt-export-field prompt-export-field-wide" : "prompt-export-field"} key={field}>
                  <span>{label}</span>
                  {multiline ? (
                    <textarea
                      onChange={(event) => updateText(field, event.target.value)}
                      ref={index === 0 ? firstFieldRef : undefined}
                      rows={field === "additional_unknowns" ? 3 : 2}
                      value={form[field]}
                    />
                  ) : (
                    <input onChange={(event) => updateText(field, event.target.value)} value={form[field]} />
                  )}
                </label>
              ))}
            </div>
            <fieldset className="prompt-export-presets">
              <legend>作成するもの (Requested outputs)</legend>
              {REQUESTED_OUTPUT_OPTIONS.map((option) => (
                <label key={option.id}>
                  <input
                    checked={form.requested_outputs.includes(option.id)}
                    onChange={(event) => updateRequestedOutput(option.id, event.target.checked)}
                    type="checkbox"
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </fieldset>
            <section className="prompt-export-unknowns" aria-labelledby="prompt-export-unknowns-title">
              <h3 id="prompt-export-unknowns-title">不明なまま残る項目 (Unknown)</h3>
              {unknowns.length > 0 ? <ul>{unknowns.map((item) => <li key={item}>{item}</li>)}</ul> : <p>なし</p>}
            </section>
          </form>
          <section className="prompt-export-preview" aria-labelledby="prompt-export-preview-title">
            <div className="prompt-export-preview-heading">
              <div>
                <h3 id="prompt-export-preview-title">Markdownプレビュー</h3>
                <p>ここで最終文面を直接編集できます。</p>
              </div>
              <div className="prompt-export-actions">
                <button onClick={regenerate} type="button">入力から再生成</button>
                <button className="prompt-export-copy" onClick={() => void copy()} type="button">Markdownをコピー</button>
              </div>
            </div>
            {stale && <p className="prompt-export-stale" role="status">フォームの変更は直接編集したプレビューへ未反映です。「入力から再生成」で上書きできます。</p>}
            <textarea
              aria-label="実装用プロンプトのMarkdownプレビュー"
              className="prompt-export-markdown"
              onChange={(event) => {
                setMarkdown(event.target.value);
                setCustomized(true);
                setCopyStatus("");
              }}
              spellCheck={false}
              value={markdown}
            />
            <p aria-live="polite" className="prompt-export-copy-status">{copyStatus}</p>
          </section>
        </div>
      </div>
    </dialog>
  );
}
