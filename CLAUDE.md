# 小さな実験室（kaitoinoue0921.github.io）

井上凱斗（自治医科大学 医学部）の個人サイト。GitHub Pages で main ブランチをそのまま配信している。ビルド工程はない（静的ファイル）。

## 書き方のきまり
- コミットメッセージは日本語で、何をどう変えたかを1行で（例: `化学ノート: 単元マップを追加`）。
- 文章は大げさな言葉を使わず、状態を正直に書く（making/index.html の方針）。
- 新しいページを公開したら `sitemap.xml` に足す。中身の薄いページは `<meta name="robots" content="noindex">` にする（AdSense 審査のため）。
- 公開ページの head には AdSense（`ca-pub-1744436882685241`）、body の最後には GoatCounter（`kaitoinoue.goatcounter.com`）と共通フッター（`<footer class="site-footer">`）を入れる。
- `life.html` と `NEXT_SESSION.md` は .gitignore 済みの私的なファイル。公開しない。

## 主な場所
- `index.html` トップ / `works/` 作ったもの一覧 / `juken/` 受験・学習 / `about/` 運営者情報 / `support/` 寄付（Stripe）
- `igakubu-roadmap/` 医学部受験ロードマップ（地域枠は `chiikiwaku/build.py` で生成）
- `works/{math,chem,physics,eng-grammar}-notes/index.html` 高校ノート。別の場所でビルドした1ファイル版（1〜2MB）。元のソースはこのリポジトリにない。
- `works/*-notes/items/` ノートを1項目1ページに分けたもの。**手で直さない**。ノートを差し替えたら `python3 tools/build_note_pages.py` で作り直す（sitemap.xml の `/items/` 行も作り直される）。
- `assets/katex/` 項目ページ用の KaTeX（ノートから抜き出したもの）
- `t/` 家庭教師の生徒用「今週の問題」（`weeks.json`）、`works/saitama-*` 埼玉大対策
- `study-map/` スタディスポットMAP（Supabase）

## 節約のきまり
- モデルは `.claude/settings.json` で `opusplan`（計画モードのときだけ Opus、作業は Sonnet）、考える量は medium、上限 high にしてある。
- 方針が決まった手作業（ページの一括生成、多数ファイルの編集、表示やリンクの確認）は、サブエージェント `worker`（Sonnet）に仕様を渡して任せる。Opus は方針決めと最後の確認だけ。
- 1つのセッションでは1つのテーマだけ。別のテーマは新しいセッションで。
- 1〜2MB の HTML は丸ごと読まない。`grep -o` や Python で必要な部分だけ取り出す。
- 見た目の確認: `python3 -m http.server 8765 --bind 127.0.0.1` を立て、`NODE_PATH=$(npm root -g) node` から Playwright（Chromium はインストール済み）でスクリーンショットを撮る。止めるときは `kill $(pgrep -f "[h]ttp.server 8765")`（`pkill -f` は自分のシェルも止める）。

## ローカルとクラウドの分担
- Search Console・AdSense・GoatCounter・Stripe など、ブラウザでログインして見る作業はローカル（Mac）の Claude がやる。やることの一覧は `.claude/local-tasks.md`。
- ローカルが書き出した Search Console の数字は `.claude/gsc/` に置かれる。クラウドではそれを読んで、タイトルや説明文を直す。
