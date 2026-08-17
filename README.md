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
- `NOVAIQ_TEXT_MODEL`（既定 `gpt-5.6-luna`）/ `NOVAIQ_IMAGE_MODEL`（既定 `gpt-image-2`）… いつでも変更可
- 画像はコスパ優先: `NOVAIQ_IMAGE_SIZE=1024x1024` / `NOVAIQ_IMAGE_QUALITY=low`

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

## 推奨: NOVAIQ Connector（ConoHa WING 等で確実に投稿する）

ConoHa WING などは前段の nginx/WAF が標準の `Authorization` ヘッダを落とすため、Application Password 認証（`/wp-json` Basic 認証）が `401 rest_not_logged_in` になることがあります。その場合は、`Authorization` に依存しない **NOVAIQ Connector**（独自ヘッダ `X-NOVAIQ-KEY` で認証）を使ってください。

1. `wordpress/novaiq-connector.php` を WordPress の `wp-content/mu-plugins/` に配置（フォルダが無ければ作成）。mu-plugins は自動有効化されます。
2. プラグイン内の `NOVAIQ_API_KEY`（`CHANGE_ME_TO_A_LONG_RANDOM_STRING`）を長いランダム文字列に変更。
3. 同じ値を、ツール側の Secrets / `.env` の `NOVAIQ_API_KEY` に設定。
4. `WP_URL` も設定。これで `NOVAIQ_API_KEY` があるときは自動的に Connector 経由（下書き作成・アイキャッチ同梱）で投稿します。

## ConoHa / WordPress で認証が通らないとき（Application Password を使う場合）

Application Password でREST APIを使うには、サーバが `Authorization` ヘッダをPHPへ渡す必要があります。ConoHa（Apache＋CGI/FastCGI）では既定でカットされることがあり、その場合 `rest_not_logged_in`（401）になります。WordPress ルートの `.htaccess` の先頭付近に次を追記してください:

```apache
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
</IfModule>
# 上で不足する環境では下も併記
SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
```

- 追記後も 401 が続く場合は、ConoHaコントロールパネルで **WAF を一時的にOFF** にして再確認してください（WAFがヘッダを除去している場合があります）。
- 本ツールは WAF のパスルール対策として、REST を `?rest_route=/wp/v2/...` 形式で呼び出します（`/wp-json/...` が 403 になる環境向け）。

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
