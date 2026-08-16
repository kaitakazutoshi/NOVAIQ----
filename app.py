"""NOVAIQ — space-themed local control panel (Streamlit)."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from novaiq.config import get_settings  # noqa: E402
from novaiq.decorate import (  # noqa: E402
    add_decoration,
    delete_decoration,
    load_decorations,
    reset_to_defaults,
)
from novaiq.pipeline import run_once  # noqa: E402
from novaiq.render import build_preview_page  # noqa: E402
from novaiq.templates.registry import GENRES, list_templates  # noqa: E402

st.set_page_config(page_title="NOVAIQ Control", page_icon="🚀", layout="wide")

# ----------------------------------------------------------------------------- styles
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Noto+Sans+JP:wght@400;700&display=swap');
.stApp {
  background:
    radial-gradient(1200px 600px at 15% -10%, rgba(124,92,255,.25), transparent 60%),
    radial-gradient(900px 500px at 110% 10%, rgba(0,180,255,.18), transparent 55%),
    linear-gradient(180deg, #05070f 0%, #0a0e1f 55%, #070a17 100%);
}
/* starfield */
.stApp::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    radial-gradient(1px 1px at 20% 30%, #fff, transparent),
    radial-gradient(1px 1px at 70% 60%, #cfd6ff, transparent),
    radial-gradient(1px 1px at 40% 80%, #fff, transparent),
    radial-gradient(2px 2px at 85% 20%, #b3a4ff, transparent),
    radial-gradient(1px 1px at 55% 15%, #fff, transparent);
  background-repeat:repeat; background-size:280px 280px; opacity:.5;
  animation:drift 60s linear infinite;
}
@keyframes drift { from{background-position:0 0;} to{background-position:280px 560px;} }
h1.novaiq-title{
  font-family:'Orbitron',sans-serif; font-weight:800; letter-spacing:.14em;
  font-size:2.6rem; margin:.2em 0 0;
  background:linear-gradient(90deg,#8fb4ff,#b3a4ff,#7c5cff);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
  text-shadow:0 0 30px rgba(124,92,255,.45);
}
.novaiq-sub{ color:#9aa3d8; letter-spacing:.28em; font-size:.8rem; text-transform:uppercase;}
section.main > div { position:relative; z-index:1; }
.stButton>button{
  background:linear-gradient(90deg,#6d3bff,#7c5cff 60%,#00b4ff);
  color:#fff; border:0; border-radius:14px; padding:.6em 1.1em; font-weight:700;
  box-shadow:0 0 24px rgba(124,92,255,.5); transition:transform .1s ease, box-shadow .2s;
}
.stButton>button:hover{ transform:translateY(-1px); box-shadow:0 0 34px rgba(124,92,255,.8);}
div[data-testid="stMetric"], .stTabs [data-baseweb="tab-panel"]{
  background:rgba(18,23,52,.55); border:1px solid rgba(124,92,255,.22);
  border-radius:16px; padding:14px 18px; backdrop-filter:blur(6px);
}
.stTabs [data-baseweb="tab"]{ font-weight:700; }
.badge-ok{ color:#5cf0b0; font-weight:700;}
.badge-no{ color:#ff8f9a; font-weight:700;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<h1 class="novaiq-title">NOVAIQ</h1>', unsafe_allow_html=True)
st.markdown('<div class="novaiq-sub">自動投稿コントロールパネル ・ auto-poster control</div>', unsafe_allow_html=True)
st.write("")

settings = get_settings()
tab_run, tab_deco, tab_conn = st.tabs(["🚀 実行", "🎨 装飾管理", "🔌 接続設定"])

# ----------------------------------------------------------------------------- RUN tab
with tab_run:
    left, right = st.columns([1, 1.3], gap="large")
    with left:
        st.subheader("設定")
        tmpl_opts = {f"{t.genre_label} / {t.name}": t.id for t in list_templates()}
        tmpl_label = st.selectbox("テンプレート", list(tmpl_opts.keys()))
        template_id = tmpl_opts[tmpl_label]

        language = st.radio(
            "論文の言語", ["en", "ja", "any"],
            index=0, horizontal=True,
            help="en=英語, ja=日本語, any=すべて（後から変更可）",
        )
        use_pubmed = st.checkbox("PubMedも併用（医学・生命科学に有効）", value=True)
        with_image = st.checkbox("アイキャッチ画像を生成", value=True)
        apply_deco = st.checkbox(
            "AFFINGER装飾を適用",
            value=True,
            help="登録済みの装飾コードを本文に埋め込みます",
        )
        dry_run = st.checkbox(
            "dry-run（WordPressに投稿せず生成物だけ確認）", value=True,
            help="OFFにすると実際に下書き(draft)を投稿します",
        )

        start = st.button("🚀 スタート", use_container_width=True, type="primary")

    with right:
        st.subheader("ログ")
        log_box = st.empty()

    if start:
        buffer: list[str] = []

        def _log(msg: str) -> None:
            buffer.append(msg)
            log_box.code("\n".join(buffer), language=None)

        with st.spinner("実行中…"):
            res = run_once(
                template_id,
                settings=settings,
                language=language,
                use_pubmed=use_pubmed,
                dry_run=dry_run,
                with_image=with_image,
                apply_deco=apply_deco,
                log=_log,
            )
        st.session_state["last_result"] = res

    res = st.session_state.get("last_result")
    if res is not None:
        st.divider()
        if res.error:
            st.error(f"失敗: {res.error}")
        elif res.ok:
            if res.dry_run:
                st.success("dry-run 完了。下のプレビューで中身を確認できます。")
            else:
                st.success(f"下書き(draft)を作成しました！ post_id = {res.wp_post_id}")
                if res.wp_edit_link:
                    st.markdown(f"[✏️ WordPressで編集する]({res.wp_edit_link})")

        if res.article and res.paper:
            c1, c2, c3 = st.columns(3)
            c1.metric("読了時間", f"{res.article.reading_time_min} 分")
            c2.metric("実践時間", f"{res.article.practice_time_min} 分")
            c3.metric("被引用数(元論文)", f"{res.paper.cited_by_count}")

            st.markdown(f"**採用した論文:** {res.paper.short_citation()}")

            if res.image_path and Path(res.image_path).exists():
                st.image(str(res.image_path), caption="アイキャッチ（プレビュー）", use_container_width=True)

            st.markdown("#### プレビュー")
            preview_html = build_preview_page(
                res.article, res.paper,
                image_rel=None,  # image shown separately above
            )
            components.html(preview_html, height=680, scrolling=True)

            cold1, cold2 = st.columns(2)
            cold1.download_button(
                "⬇ 記事HTMLをダウンロード", res.post_html, file_name="post.html", mime="text/html"
            )
            cold2.download_button(
                "⬇ 記事JSONをダウンロード",
                res.article.model_dump_json(indent=2),
                file_name="article.json",
                mime="application/json",
            )

# ----------------------------------------------------------------------------- DECO tab
with tab_deco:
    st.subheader("装飾コードの登録（AFFINGER等）")
    st.info(
        "AFFINGER の装飾を「名前＋コード」で登録します。"
        "コードには本文が入る位置に **`{content}`** を入れてください。\n\n"
        "下書きID 14（パーツ確認用）からよく使うものを初期登録済みです。"
        "全ショートコードのカタログは `data/affinger_catalog.json` に保存してあります。"
        "よく使うものを後から教えてもらえれば、有効/無効を切り替えます。",
        icon="🎨",
    )
    with st.form("add_deco", clear_on_submit=True):
        dc1, dc2 = st.columns([1, 2])
        name = dc1.text_input("装飾の名前", placeholder="マーカー")
        code = dc2.text_input("コード（{content} を含む）", placeholder="[st-marker]{content}[/st-marker]")
        desc = st.text_input("メモ（任意）", placeholder="重要な一文を黄色マーカーに")
        submitted = st.form_submit_button("＋ 登録 / 更新")
        if submitted:
            if not name or "{content}" not in code:
                st.error("名前を入力し、コードには {content} を必ず含めてください。")
            else:
                add_decoration(name, code, desc)
                st.success(f"登録しました: {name}")

    st.markdown("#### 登録済みの装飾")
    if st.button("AFFINGER初期セットに戻す"):
        reset_to_defaults()
        st.rerun()
    decos = load_decorations()
    if not decos:
        st.caption("まだ登録がありません。")
    for d in decos:
        cols = st.columns([2, 4, 3, 1])
        cols[0].markdown(f"**{d.name}**")
        cols[1].code(d.code, language=None)
        cols[2].caption(d.description or "—")
        if cols[3].button("削除", key=f"del_{d.name}"):
            delete_decoration(d.name)
            st.rerun()

# ----------------------------------------------------------------------------- CONN tab
with tab_conn:
    st.subheader("接続状態")

    def _badge(ok: bool) -> str:
        return '<span class="badge-ok">● 設定済み</span>' if ok else '<span class="badge-no">● 未設定</span>'

    st.markdown(f"OpenAI APIキー: {_badge(settings.has_openai)}", unsafe_allow_html=True)
    st.markdown(
        f"NOVAIQ Connector（推奨）: {_badge(settings.has_connector)}", unsafe_allow_html=True
    )
    st.markdown(
        f"WordPress Application Password: {_badge(settings.has_wordpress)}",
        unsafe_allow_html=True,
    )
    st.caption(
        f"テキストモデル: `{settings.text_model}` ／ 画像モデル: `{settings.image_model}`"
    )
    st.caption(
        "Secrets: `OPENAI_API_KEY`, `WP_URL`, `NOVAIQ_API_KEY`（推奨）または "
        "`WP_USERNAME`/`WP_APP_PASSWORD`"
    )

    if st.button("WordPress 接続テスト"):
        try:
            if settings.has_connector:
                from novaiq.publish import ConnectorClient

                info = ConnectorClient(settings).check_connection()
                st.success(
                    f"Connector 接続OK: {info.get('site', '?')} / admin={info.get('admin', '?')}"
                )
            elif settings.has_wordpress:
                from novaiq.publish import WordPressClient

                me = WordPressClient(settings).check_connection()
                st.success(f"接続OK: {me.get('name', '?')}（id={me.get('id')}）")
            else:
                st.error("接続情報が未設定です（NOVAIQ_API_KEY か WP_APP_PASSWORD）。")
        except Exception as exc:
            st.error(f"接続失敗: {exc}")

    st.divider()
    st.markdown("**ジャンル一覧（更新比率の土台）**")
    st.write("、".join(GENRES.values()))
