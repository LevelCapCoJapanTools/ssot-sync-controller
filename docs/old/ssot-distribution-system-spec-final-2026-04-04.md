# SSOT / Skills / MCP 配付 全体整理（最終確定版・2026-04-04）

# 1. 背景

複数の案件リポジトリへ SSOT / Skills / MCP を人手でコピーして配る方式は、更新漏れ、差分見落とし、案件ごとの差異、AI エージェントの挙動不一致を引き起こす。
さらに、同期ロジックを各案件 repo に持たせると、ロジック更新が各 repo に波及し、運用が破綻する。

このため、本システムでは次を原則とする。

* 各 repo は **何を使うかだけ** 宣言する
* 同期ロジックは **ssot-sync-controller** に中央集約する
* GitHub への変更反映は **GitHub App 認証**で行う
* 差分は **PR 作成型**で提示する
* version は **固定**し、自動 latest 追従しない
* rollback は **手動**で行う

---

# 2. 初期に確定していた大方針

以下は、最初に確定していた大方針であり、本版でも維持する。

* pull型（各 repo Actions）
* ssot-bot認証
* PR作成型
* version固定
* セット方式
* 完全分離 / 固定パス
* rollbackは手動

ただし、このうち「セット方式」の具体表現は、旧版では `include + regex` としていたが、最終確定では **include only + glob only** に補正された。
この補正は本書で明示的に反映する。

---

# 3. 旧版からの置換・補正一覧

## 3.1 セット定義の表現

### 旧版

* include only
* regex 対応

### 最終確定

* include only
* **glob only**
* regex は使わない

## 3.2 セット依存

### 旧版

* セット依存あり
* DAG 前提
* 最大深さ 3

### 最終確定

* **セット依存は禁止**
* `set:` 記法は存在しない
* `dependencies:` も存在しない
* 1 セットはそれ単体で完結する

## 3.3 同一ターゲットパス衝突時

### 旧版

* エラー停止

### 最終確定

* **後勝ち（最後勝ち）**
* include を上から順に評価し、後に来たものが最終状態になる
* ただし、そもそも衝突するようなカタログを作らないのは**運用規約**で担保する

## 3.4 ルート直下ファイル名

### 過去の会話中に誤って出たもの

* `Agent.md`
* `Gemini.md`
* `agent.md`
* `gemini.md`

### 最終確定

* **`AGENTS.md`**
* **`CLAUDE.md`**
* **`GEMINI.md`**
* **`.agent.md`**

## 3.5 `.github/**` の扱い

### 旧版・途中案

* `.github/**` を広く許可

### 最終確定

* `.github/**` は採用しない
* **許可する `.github` 配下を個別列挙**する
* `.github/workflows/**` は非対象のままとする

## 3.6 Skills / MCP のコピー先写像

### 途中案

* ssot-sync-controller が AI 種別ごとに path を写像する

### 最終確定

* **catalog のパスをそのまま保持して target repo に置く**
* そのため、出力先構造が異なる系統は、**物理的にカタログ repo を分ける**
* ssot-sync-controller は path remap をしない

---

# 4. 全体目的

本システムの目的は次の通り。

1. 各案件 repo が必要な SSOT / Skills / MCP だけを宣言的に取り込めるようにする
2. 同期ロジックを中央に寄せて、各 repo にロジックを分散させない
3. bot 名義の PR として差分を提示し、人間がレビュー・マージできるようにする
4. version 固定で壊れた変更の自動追従を防ぐ
5. rollback を人間主導に固定し、安全性と可観測性を保つ
6. 実装 Agent が推論不要で実装できるレベルまで仕様を固定する

---

# 5. システム全体構成

```text
┌────────────────────────────────────────────┐
│ target repos（各案件 repo）               │
│                                            │
│ - ssot-bot.yml                             │
│ - GitHub Actions                           │
│   - schedule                               │
│   - workflow_dispatch                      │
└───────────────────────┬────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────┐
│ ssot-sync-controller                                  │
│                                            │
│ - 設定読込                                 │
│ - catalog checkout                         │
│ - セット定義読込                           │
│ - include 展開                             │
│ - dedupe                                   │
│ - desired state 生成                       │
│ - 上書き / 削除差分生成                    │
│ - JSON 指示生成（BASE64済）                │
└───────────────────────┬────────────────────┘
                        │ ssot-bot 認証を使用
                        ▼
┌────────────────────────────────────────────┐
│ GitHub App                                 │
│                                            │
│ - JWT 生成                                 │
│ - Installation Token 取得                  │
│ - GitHub API 実行                          │
│   - branch作成                             │
│   - commit                                 │
│   - push                                   │
│   - pull request 作成                      │
└───────────────────────┬────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────┐
│ GitHub                                     │
│ - branch                                   │
│ - commit                                   │
│ - pull request                             │
└────────────────────────────────────────────┘
```

---

# 6. リポジトリ一覧

| repo | 役割 |
| --- | --- |
| `ssot-sync-controller` | 中央同期ロジック |
| `ssot-bot` | GitHub 操作の認証を担当する実行主体 |
| `ssot-core` | AI 共通ルール、入口ファイル、共通 SSOT 実体 |
| `ssot-schema` | Plan / Skill / Tool の設計スキーマ、および運用ルール系 SSOT |
| `ssot-policies` | セキュリティ、禁止事項、環境制約などのポリシー系 SSOT |
| `skills-core` | 汎用スキル実体とセット定義 |
| `skills-provider` | provider 差分を持つスキル実体とセット定義 |
| `skills-domain` | ドメイン固有スキル実体とセット定義 |
| `mcp-server-core` | MCP 実行基盤の実体とセット定義 |
| `mcp-tools` | MCP tool 定義の実体とセット定義 |
| `infra-runtime` | 非機密の runtime 定義、deploy 手順、IaC template |
| `adapter-layer` | OS / shell / path 差分吸収用の補助レイヤ |
| `skill-catalog` | DESIGN 時にだけ参照する索引リポジトリ |
| `test-simulation` | DESIGN / 検証時に使う dry-run / fault injection 資産 |
| `template-repo` | 新規 repo 雛形 |
| `target repos` | 実案件 repo |

## 6.1 細分化後の基本ルール

* 配付方式は変えず、catalog path をそのまま target repo にコピーする
* 物理 repo の主基準は **path / 権限境界** とする
* 役割名による細分化は採用してよいが、**同じ target path を複数 repo で共有しない**
* 1 つの SSOT セットの中に、**Copilot / Claude / GeminiCLI / Cursor / Codex** 向け入口 path をまとめて持たせてよい
* AI 別入口 path は **`ssot-core` が一元管理**する
* 他 repo は、`catalog-path-ownership-draft.md` の「対応する AI と主入口 path」および「補助入口 / 参照入口」に載る path と同じ target path に配置しない
* `skill-catalog` と `test-simulation` は **配付対象ではなく**、DESIGN / 検証時のみ使う
* `adapter-layer` は `skills-*` / `mcp-*` の下位で OS / shell / path 差分だけを吸収する補助 repo とする

## 6.2 担当 path の最小固定範囲

* すべての path を最初に固定する必要はない
* ただし、`.github/` 配下や入口ファイルなど、衝突しやすい path は先に担当 repo を固定する
* 初期ドラフトは `catalog-path-ownership-draft.md` に表形式でまとめる

---

# 7. target repo 側仕様

## 7.1 `ssot-bot.yml`

`ssot-bot.yml` は **最小構成のみ**を持つ。

```yaml
version: 1

use:
  - name: ssot/react-app
    ref: v1.2.0

  - name: skills/copilot-frontend
    ref: v2.0.0

  - name: mcp/basic-tools
    ref: v1.0.0
```

## 7.2 ルール

* `version` は固定値 `1`
* `use` は配列
* 各要素は `name` と `ref` のみ
* `name` は `<domain>/<kebab-case>`
* `ref` は固定 version（tag / branch / commit）
* フィールド追加禁止
* override 禁止
* 条件分岐禁止
* repo 側は **何を使うかだけ** を宣言する

---

# 8. GitHub Actions 側仕様

## 8.1 トリガー

* `schedule`
* `workflow_dispatch`

## 8.2 `workflow_dispatch`

* **入力なし**
* 手動実行は「タイミング」のみを制御する
* 実行内容は `ssot-bot.yml` のみに依存する

## 8.3 排他制御

* GitHub Actions の `concurrency` のみで排他する
* ssot-sync-controller 内ロックは持たない
* Redis ロック、ファイルロック、DB ロックは持たない

例:

```yaml
concurrency:
  group: ssot-sync-${{ github.repository }}
  cancel-in-progress: false
```

## 8.4 同時実行時の扱い

* 同一 repo で同時実行は 1 つだけ
* 2 つ目以降は待機
* 実行中ジョブは途中キャンセルしない

---

# 9. ssot-sync-controller と ssot-bot の責務境界

## 9.1 原則

```text
ssot-sync-controller = 「何をするか決め、完全な材料を作る頭脳」
ssot-bot = 「GitHub に対して操作する身分証・実行主体」
```

## 9.2 ssot-sync-controller の責務

* `ssot-bot.yml` 読込
* catalog checkout
* セット定義読込
* include 展開
* dedupe
* 最終 desired state 決定
* 上書き / 削除対象決定
* branch 名決定
* commit message 決定
* PR title / body 材料決定
* JSON 指示生成
* `content` の BASE64 化

## 9.3 ssot-bot の責務

* GitHub App JWT 生成
* Installation Token 取得
* GitHub API 実行

  * branch 作成
  * commit 作成
  * push
  * PR 作成

## 9.4 NG

* ssot-bot が差分計算しない
* ssot-bot がセット解決しない
* ssot-bot が BASE64 変換しない
* ssot-sync-controller が曖昧な材料を渡さない
* ssot-sync-controller が raw content を渡して ssot-bot 側に加工させない

---

# 10. ssot-sync-controller → ssot-bot インターフェース仕様

```json
{
  "repo": "owner/repo-name",
  "base_branch": "main",
  "head_branch": "ssot/sync-20260404-120001",
  "commit": {
    "message": "chore(ssot): sync ssot-core@v1.2.3 [20260404-120001]",
    "files": [
      {
        "path": ".github/copilot-instructions.md",
        "content": "BASE64_ENCODED_CONTENT",
        "mode": "100644"
      },
      {
        "path": "obsolete/file.md",
        "delete": true
      }
    ]
  },
  "pull_request": {
    "title": "chore(ssot): sync ssot-core@v1.2.3 [20260404-120001]",
    "body": "...",
    "labels": ["ssot", "auto-generated"]
  }
}
```

## 10.1 ルール

* `content` は **ssot-sync-controller が BASE64 化**する
* `content` と `delete` は同時に持てない
* `path` は相対パスのみ
* 先頭 `/` 禁止
* `..` 禁止
* `files` が空なら ssot-bot は何もしない
* rename は持たず `delete + add` で扱う

---

# 11. ブランチ・PR 命名規則

## 11.1 ブランチ名

```text
ssot/sync-YYYYMMDD-HHMMSS
```

## 11.2 ブランチ衝突時

* **エラー**
* retry しない
* 次回実行に任せる
* そもそも重複しない命名を前提にする

## 11.3 PR タイトル

```text
chore(ssot): sync <source>@<version> [YYYYMMDD-HHMMSS]
```

例:

```text
chore(ssot): sync ssot-core@v1.2.3 [20260404-120001]
```

## 11.4 既存 PR がある場合

* 更新しない
* 再利用しない
* close しない
* **毎回新規 PR** を作成する

---

# 12. PR 本文テンプレート

## 12.1 方針

* PR 本文は固定フォーマット
* target repo 側のテンプレートを使う

## 12.2 テンプレートファイル名

```text
.github/PULL_REQUEST_TEMPLATE/ssot-sync.md
```

## 12.3 役割分担

| 項目        | 担当          |
| --------- | ----------- |
| テンプレート構造  | target repo |
| 埋め込むデータ   | ssot-sync-controller   |
| PR API 実行 | ssot-bot  |

## 12.4 PR 本文に含める情報

* Source（利用セット + version）
* Changes（更新件数 / 削除件数）
* Diff Summary（対象パス）
* Warnings（存在しない include 等）
* 自動生成である旨

---

# 13. 固定パス設計（target repo への配付先）

## 13.1 基本方針

* `.ssot/` のような単一隔離ディレクトリには集約しない
* **repo 内の用途別ディレクトリに分散**する
* ただし、どこにでも書いてよいわけではなく、**ssot-sync-controller 内ホワイトリスト**で中央制御する

## 13.2 ホワイトリストの実体

ホワイトリストは **ssot-sync-controller 内ファイル**で管理する。

例:

```yaml
# ssot-sync-controller/config/allowed-paths.yml
  allowed:
    - docs/**
    - .github/copilot/**
    - .github/copilot-instructions.md
    - .github/instructions/**
    - .github/agents/**
    - .cursor/rules/**
    - .github/PULL_REQUEST_TEMPLATE/ssot-sync.md
    - .claude/**
    - .agent.md
    - AGENTS.md
    - CLAUDE.md
    - GEMINI.md
```

## 13.3 ルール

* 書き込み可能なのは `allowed` に一致したパスのみ
* allowed 外は絶対に触らない
* 既存ファイルは上書き
* 不要ファイルは削除
* ホワイトリスト配下は **完全同期領域**
* ルート直下 `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / `.agent.md` も完全支配対象
* `.github/workflows/**` は**非対象**であり、ホワイトリストに含めない

## 13.4 実質意味

ホワイトリストに入った場所は、

* 人手編集しても上書きされうる
* セットから外れたら削除されうる
* SSOT 管理領域である

---

# 14. 差分生成と同期方式

## 14.1 desired state

* 選択されたセット群から**最終状態**を導出する
* target repo の管理対象領域を、その最終状態に一致させる

## 14.2 上書き

* 同一パスの既存ファイルは上書きする

## 14.3 削除

* セット変更で不要になったファイルは削除する
* ホワイトリスト配下は完全同期対象とする
* ルート直下ファイルも完全支配とする

## 14.4 大量変更

* 制限なし
* PR 分割なし
* システム側で抑制しない

---

# 15. 共通 include 展開ルール

## 15.1 表現

* YAML
* include のみ
* glob のみ

## 15.2 評価順序

* include は**上から順に評価**する

## 15.3 重複

* 同一内容・同一対象は dedupe して 1 回だけ取り込む
* 同一対象への複数入力は **後勝ち**

## 15.4 存在しない include パス

* エラー停止しない
* **警告**とする
* GitHub Actions ログに出す
* PR 本文にも記録する

## 15.5 空 include

* 空セットは許容
* 何もしない

## 15.6 セット依存

* 禁止
* `set:` なし
* `dependencies:` なし

---

# 16. SSOT catalog 設計

## 16.1 配置方針

SSOT は `ssot-core` / `ssot-schema` / `ssot-policies` に細分化してよい。  
ただし、**同じ target path を複数 repo で共有しない**ことを前提とする。

```text
ssot-core/
  react-app/
    set.yml
    AGENTS.md
    CLAUDE.md
    GEMINI.md
    .agent.md
    .github/copilot-instructions.md
    .cursor/rules/
      ...
    .github/copilot/
      ...
ssot-schema/
  agile/
    set.yml
    .github/instructions/
      ...
ssot-policies/
  rentalserver/
    set.yml
    .github/copilot/
      40-testing-strategy.md
      50-security.md
```

## 16.1.1 責任分担

* `ssot-core` は AI 別入口ファイル群の最終責任者とする
* `ssot-schema` / `ssot-policies` は**担当ファイルを丸ごと差し替える単位**として扱う
* 1 ファイルの一部だけを複数 repo から合成しない
* 例: `40-testing-strategy.md` を `ssot-policies` が担当する場合、そのファイル全体を管理し、章単位の部分上書きは行わない

## 16.2 セット定義ファイル名

* `set.yml`

## 16.3 `set.yml` 構造

```yaml
include:
  - AGENTS.md
  - CLAUDE.md
  - GEMINI.md
  - .agent.md
  - .github/copilot-instructions.md
  - .cursor/rules/**
  - docs/**
```

## 16.4 include 基準

* **`set.yml` からの相対パス**

## 16.5 コピー規則

* include に列挙された path を、その**相対位置のまま** target repo に置く
* ssot-sync-controller 側で path remap はしない
* `ssot-core` / `ssot-schema` / `ssot-policies` 間で同じ target path を共有しない

---

# 17. Skills catalog 設計

## 17.1 物理 repo 分割

* 出力先構造が異なる系統は、**物理的に catalog repo を分ける**
* 例:

  * `skills-core`
  * `skills-provider`
  * `skills-domain`

> ここで重要なのは、**ssot-sync-controller が AI 種別ごとに path remap しない**こと。
> 出力先 path の違いは、catalog repo 側の構造で表現する。

## 17.2 配置方針

```text
skills-core/
  sets/
    frontend-ui.yml
    backend-php.yml
  <managed paths>/
    ...
```

## 17.3 セット定義形式

* YAML
* include のみ
* glob のみ
* セット依存なし

## 17.4 include 基準

* **catalog ルート基準**

## 17.5 include 単位

* **ディレクトリ単位コピー**

例:

```yaml
include:
  - .github/copilot/**
  - .claude/agents/**
```

## 17.6 コピー規則

* **catalog の path をそのまま保持して** target repo に置く
* ssot-sync-controller は path remap しない

## 17.7 Skills の責務境界

* `skills-core` は汎用スキルを持つ
* `skills-provider` は provider 固有の業務操作を持つ
* `skills-domain` はアプリ固有の操作を持つ
* `adapter-layer` は OS / shell / path 差分吸収に限定し、provider 固有の業務操作は持たない

---

# 18. MCP catalog 設計

## 18.1 物理 repo 分割

* Skills と同様、出力先構造が異なる系統は物理 repo を分ける
* 例:

  * `mcp-server-core`
  * `mcp-tools`

## 18.2 配置方針

```text
mcp-tools/
  sets/
    basic.yml
    full.yml
  <managed paths>/
    ...
```

## 18.3 セット定義形式

* YAML
* include のみ
* glob のみ
* セット依存なし

## 18.4 include 基準

* **catalog ルート基準**

## 18.5 include 単位

* **ディレクトリ単位コピー**

例:

```yaml
include:
  - .claude/mcp/**
  - docs/mcp/**
```

## 18.6 コピー規則

* **catalog の path をそのまま保持して** target repo に置く
* ssot-sync-controller は path remap しない

## 18.7 補助 repo の扱い

* `infra-runtime` は非機密の runtime 定義、deploy 手順、IaC template だけを持つ
* `infra-runtime` に secret 実値は含めない
* `adapter-layer` は実行差分吸収の補助 repo とし、target path は `skills-*` / `mcp-*` と重ねない
* `skill-catalog` は DESIGN 時に Planner だけが参照する索引 repo であり、配付対象ではない
* `test-simulation` は DESIGN / 検証時の dry-run / fault injection 資産であり、標準の配付対象ではない

---

# 19. カタログ品質と衝突方針

## 19.1 原則

* 衝突するようなカタログを作らない
* これは**仕組みではなく規約**で担保する

## 19.2 仕組み上の挙動

* 同一対象に複数入力が来た場合は **後勝ち**
* ssot-sync-controller はそのままストリーム評価する
* 衝突防止ロジックは持たない

## 19.2.1 設計時の確認

* 後勝ちは**例外時の逃げ道**であり、平常運用で前提にしない
* Planner は DESIGN 時に、repo 間の内容相性を確認する
* `skill-catalog` のような索引 repo は DESIGN 時だけ参照し、controller は実行時に参照しない

## 19.2.2 path 担当の最小固定

* 入口ファイルや `.github/` 配下など、衝突しやすい path は先に担当 repo を固定する
* 初期ドラフトは `catalog-path-ownership-draft.md` を参照する

## 19.3 意味

* ルール違反はカタログ側設計ミス
* ssot-sync-controller 側は軽量・単純に保つ

---

# 20. ロールバック戦略

## 20.1 方針

* **手動 rollback**
* 自動 rollback はしない
* 別専用コマンドも持たない

## 20.2 手順

1. 問題の PR を revert
2. schedule を一時停止
3. `ssot-bot.yml` の version を手動で戻す
4. 必要なら manual 実行
5. 問題解消後に schedule 再開

---

# 21. GitHub App 権限

会話で確定した採用権限は次の通り。

* `Contents: Read & Write`
* `Pull requests: Read & Write`
* `Actions: Read`
* `Secrets: Read`
* `Metadata: Read`

## 21.1 位置づけ

* `Contents RW` は branch / commit / push に必要
* `Pull requests RW` は PR 作成に必要
* `Secrets Read` は org secrets / repo secrets fallback 確認のため採用
* `Actions Read` は workflow / Actions 関連情報の参照余地として採用
* `Metadata Read` は repo 情報取得のため必要

## 21.2 `.github/workflows/**` を非対象にする意味

* workflow files まで配付対象にすると、GitHub App 側で `Workflows` permission が必要になる
* 本設計では `.github/workflows/**` を非対象とするため、workflow files 更新権限は要求しない

---

# 22. 非対象

* `.github/workflows/**` の配付
* アプリケーションコード配付
* 双方向同期
* target repo 側からの差分逆流
* 自動 rollback
* 既存 PR 更新
* `skill-catalog` の直接配付
* `test-simulation` の標準配付
* secret 実値を含む設定ファイルの配付

---

# 23. ログ・監査

* GitHub Actions ログ
* PR 本文
* PR 差分

存在しない include、空展開、削除件数などは PR と Action ログに残す。

---

# 24. 完全確定事項一覧（要約表）

| 項目                | 最終確定                                                     |
| ----------------- | -------------------------------------------------------- |
| 同期方式              | Pull 型                                                   |
| 実行起点              | 各 repo の Actions                                         |
| 認証                | GitHub App                                               |
| 反映方式              | PR 作成型                                                   |
| version           | 固定                                                       |
| rollback          | 手動                                                       |
| repo 設定           | `ssot-bot.yml` 最小構成                                      |
| set 定義            | YAML / include only / glob only                          |
| set 依存            | 禁止                                                       |
| include 評価        | 上から順                                                     |
| 重複                | dedupe                                                   |
| 衝突                | 後勝ち                                                      |
| missing include   | 警告                                                       |
| empty include     | 許容                                                       |
| 書込範囲              | ssot-sync-controller ホワイトリスト                                        |
| 既存ファイル            | 上書き                                                      |
| 不要ファイル            | 削除                                                       |
| ルート直下             | 完全支配                                                     |
| workflow_dispatch | 入力なし                                                     |
| 排他                | Actions concurrency のみ                                   |
| 大量変更              | 制限なし                                                     |
| PR ブランチ           | `ssot/sync-YYYYMMDD-HHMMSS`                              |
| ブランチ衝突            | エラー                                                      |
| PR タイトル           | `chore(ssot): sync <source>@<version> [YYYYMMDD-HHMMSS]` |
| 既存 PR             | 常に新規作成                                                   |
| PR テンプレ           | `.github/PULL_REQUEST_TEMPLATE/ssot-sync.md`             |
| BASE64 化          | ssot-sync-controller 責務                                             |
| SSOT include 基準   | `set.yml` 相対                                             |
| Skills include 基準 | catalog ルート基準                                            |
| MCP include 基準    | catalog ルート基準                                            |
| Skills / MCP コピー先 | catalog path をそのまま保持                                     |
| AI 別入口 path          | `catalog-path-ownership-draft.md` を参照 |
| SSOT 物理分割         | `ssot-core` / `ssot-schema` / `ssot-policies`（同一 path 共有禁止） |
| 共通入口ファイル責任者      | `ssot-core`                                               |
| skills / provider / domain | 役割分割。ただし path / 権限境界を主基準とする                     |
| MCP 物理分割          | `mcp-server-core` / `mcp-tools`                          |
| `skill-catalog`    | DESIGN 時のみ参照、配付対象外                                       |
| `infra-runtime`    | 非機密 template / placeholder のみ配付対象                        |
