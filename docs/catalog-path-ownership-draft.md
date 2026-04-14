# catalog 担当 path 一覧（ドラフト）

このドラフトは、`ssot-distribution-system-spec-final-2026-04-04.md` の「細分化後の基本ルール」を補うための初期表である。  
最初から全 path を固定するのではなく、**衝突しやすい共通 path を先に固定する**ために使う。  
前提として、1 つの SSOT セットの中に **Copilot / Claude / GeminiCLI / Cursor / Codex** 向けの入口 path をまとめて持たせる。

## 対応する AI と主入口 path

| AI | 主入口 path | 担当 repo | 備考 |
| --- | --- | --- | --- |
| Copilot | `.github/copilot-instructions.md` | `ssot-core` | Copilot 向けの共通入口 |
| Claude | `CLAUDE.md` | `ssot-core` | Claude 向けの共通入口 |
| GeminiCLI | `GEMINI.md` | `ssot-core` | GeminiCLI 向けの共通入口 |
| Cursor | `.cursor/rules/**` | `ssot-core` | Cursor 向けルール群 |
| Codex | `AGENTS.md` | `ssot-core` | Codex 向けの共通入口 |

## 補助入口 / 参照入口

| path | 対象 | 担当 repo | 備考 |
| --- | --- | --- | --- |
| `.agent.md` | CopilotCLI などの CLI 系サブエージェント | `ssot-core` | 補助的に参照する入口として扱う |
| `.github/copilot/00-index.md` | Copilot | `ssot-core` | Copilot SSOT の参照入口 |

## SSOT 系の初期固定 path

| path | 効く AI / 用途 | 担当 repo | 備考 |
| --- | --- | --- | --- |
| `.github/copilot-instructions.md` | Copilot | `ssot-core` | Copilot の共通入口 |
| `.github/copilot/00-index.md` | Copilot | `ssot-core` | Copilot SSOT の参照入口 |
| `.github/copilot/10-requirements.md` | Copilot | `ssot-core` | Copilot 共通ガイド |
| `.github/copilot/20-architecture.md` | Copilot | `ssot-core` | Copilot 共通ガイド |
| `.github/instructions/**` | Copilot custom instructions | `ssot-schema` | 実装・運用ルール |
| `.github/copilot/40-testing-strategy.md` | Copilot テスト方針 | `ssot-policies` | ポリシー |
| `.github/copilot/50-security.md` | Copilot セキュリティ方針 | `ssot-policies` | ポリシー |
| `CLAUDE.md` | Claude | `ssot-core` | Claude 用入口 |
| `GEMINI.md` | GeminiCLI | `ssot-core` | GeminiCLI 用入口 |
| `AGENTS.md` | Codex | `ssot-core` | Codex 用入口 |
| `.agent.md` | CopilotCLI などの CLI 系サブエージェント | `ssot-core` | 補助入口 |
| `.cursor/rules/**` | Cursor | `ssot-core` | Cursor 用ルール群 |

## Skills / MCP / Infra 系の初期固定 path

| path | 担当 repo | 備考 |
| --- | --- | --- |
| `.claude/agents/common/**` | `skills-core` | 複数案件で再利用する汎用スキル |
| `.claude/agents/domain/**` | `skills-domain` | 特定アプリや案件に閉じるスキル |
| `.claude/mcp/**` | `mcp-tools` | tool 定義 |
| `docs/mcp/**` | `mcp-server-core` | MCP 実行基盤の説明資産 |
| `infra/**` | `infra-runtime` | 非機密 template / placeholder のみ |
| `adapters/**` | `adapter-layer` | OS / shell / path 差分吸収 |

## 運用ルール

* この表にない path は、repo 追加時に段階的に決める
* 同じ path を複数 repo が担当しない
* `skill-catalog` と `test-simulation` は target repo へ直接コピーしない
* Copilot 向け path と、Claude / GeminiCLI / Cursor / Codex 向け path は、**同じ SSOT セットの中に共存してよい**
* 各 AI 専用 path は、表の「効く AI / 用途」列で明確に区別する
