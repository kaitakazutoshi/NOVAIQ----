# NOVAIQ 自動投稿ツール

自己啓発×論文を、読みやすい記事にして WordPress へ自動で **下書き(draft)** 投稿するツールです。

**フロー:** 論文サイト（OpenAlex / PubMed）から引用数の多い論文を取得 → OpenAI(ChatGPT) API で日本語記事を生成 → WordPress REST API で下書き投稿。宇宙感のあるローカル Web UI（Streamlit）から操作します。

> Phase 1 の対象: パフォーマンス「A：論文1本解説（無料）」・装飾なし・下書き投稿。
> テンプレートは `src/novaiq/templates/registry.py` に追記するだけで各ジャンル3種（計15）へ拡張できます。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

環境変数を設定します（`.env.example` を `.env` にコピー、または Secrets に登録）:

- `OPENAI_API_KEY` … 記事・画像生成に必要
- `WP_URL` / `WP_USERNAME` / `WP_APP_PASSWORD` … 下書き投稿に必要（アプリケーションパスワード）
- `NOVAIQ_TEXT_MODEL`（既定 `gpt-4o`）/ `NOVAIQ_IMAGE_MODEL`（既定 `gpt-image-1`）… いつでも変更可

## 使い方

### Web UI（推奨）

```bash
streamlit run app.py
```

- **🚀 実行**: テンプレ・言語などを選び「スタート」。`dry-run` ON なら投稿せず生成物だけ確認、OFF で下書き投稿。
- **🎨 装飾管理**: AFFINGER 等の装飾を「名前＋コード（`{content}` を含む）」で登録（Phase 1 では未適用）。
- **🔌 接続設定**: OpenAI / WordPress の設定状況の確認と接続テスト。

### CLI（ヘッドレス）

```bash
python cli.py --list                          # テンプレ一覧
python cli.py --template performance_A --dry-run
python cli.py --template performance_A --no-dry-run   # 実際に下書き投稿
```

生成物は `output/`（`article.json` / `preview.html` / `eyecatch.png`）に出力されます。

## 構成

```
app.py                     # Streamlit UI（コントロールパネル）
cli.py                     # コマンドライン実行
src/novaiq/
  config.py                # 設定（環境変数）
  models.py                # Paper / Article データモデル
  sources/                 # OpenAlex / PubMed 取得
  templates/registry.py    # ジャンル×テンプレ定義（ここに追記で増設）
  generate/                # 記事生成（OpenAI）＋モック＋画像
  decorate/                # 装飾マッピング（名前→コード）
  publish/wordpress.py     # WordPress REST（下書き・画像アップ）
  state/                   # 投稿済み論文の重複防止（SQLite）
  render.py                # 最終HTML＋プレビュー生成
```
