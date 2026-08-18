# NOVAIQ

自己啓発×論文の日本語記事を生成し、WordPress へ下書き投稿するツールです。
標準の使い方は `README.md` を参照してください。

## Cursor Cloud specific instructions

- 記事生成・アイキャッチ生成は OpenAI クレジットを使う。ユーザーが明示的に許可したときだけ API を呼ぶ。
- WordPress 投稿は NOVAIQ Connector（`wordpress/novaiq-connector.php` を `wp-content/mu-plugins/` に置く）経由。既存下書きの本文差し替えは Connector の `/update` が必要。プラグインを更新したあとに `/ping` が通るか確認する。
- アイキャッチ既定サイズは横長 `1536x1024`。背景は黒/白が主で、たまに赤・黄。写真を使う場合はぼかし必須（文字が沈まないように）。
- 装飾は `<span data-deco="名前">` のみ。入れ子禁止。モデルが「ポイント：」とラベルを本文に書いた場合は適用時に削る。残った `data-deco` タグは剥がす。
- 「この記事でわかること」を箇条書きにする場合は最大3個。見出しのように読める短文にする。
- ①②③は `<ol>` に変換する（生成プロンプトでも要求し、適用前にも変換する）。
- 下書きの確認は WordPress 管理画面のプレビューで行う。AFFINGER のショートコードは公開テーマ上で描画される。
