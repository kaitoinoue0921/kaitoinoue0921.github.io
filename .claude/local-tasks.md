# ローカル（Mac の Claude）でやること

クラウドのセッションには、ブラウザも Google のログインもない。Search Console・AdSense・GoatCounter・Stripe のように画面を開く作業は、ここに書いてローカルでやる。
終わった項目は `[x]` にしてコミットする（クラウド側がそれを見て次に進む）。

## 1. 公開（最初に1回）
- [x] `claude/bold-brahmagupta-qeg5jp` ブランチを main に取り込んで push する
  ```
  git fetch origin
  git checkout main && git pull
  git merge origin/claude/bold-brahmagupta-qeg5jp
  git push origin main
  ```
- [x] 1〜2分待って、次のページが開くことを確かめる
  - https://kaitoinoue0921.github.io/works/chem-notes/items/
  - https://kaitoinoue0921.github.io/works/chem-notes/items/ch-matter-pure.html（化学式が描画されているか）
  - https://kaitoinoue0921.github.io/works/math-notes/items/patterns.html（着眼点まとめ）

## 2. Google Search Console（公開した日に）
- [x] 「サイトマップ」で `sitemap.xml` を送信し直す。状態が「成功」になり、検出された URL が 955 前後になることを確かめる
- [x] 「URL 検査」で次の URL を1つずつ入れ、「インデックス登録をリクエスト」を押す（1日の上限があるので、この順で入るところまで）
  1. https://kaitoinoue0921.github.io/juken/
  2. https://kaitoinoue0921.github.io/works/math-notes/items/
  3. https://kaitoinoue0921.github.io/works/chem-notes/items/
  4. https://kaitoinoue0921.github.io/works/physics-notes/items/
  5. https://kaitoinoue0921.github.io/works/eng-grammar-notes/items/
  6. 各ノートの `items/patterns.html`（4つ）

## 3. Search Console（2〜3週間後）
- [ ] 「ページ」レポートで、登録済みのページ数と「検出 - インデックス未登録」の数を下の記録欄に書く
- [ ] 「検索パフォーマンス」→ 期間「28日間」→「ページ」タブを、表示回数の多い順に上位30件 CSV でエクスポートし、`.claude/gsc/YYYY-MM-DD-pages.csv` に保存してコミットする
  - 「クエリ」タブは書き出さない（このリポジトリは公開なので、ページ別の数字だけにする）
  - クラウドの Claude がこれを読んで、表示はあるのにクリックされないページのタイトルと説明文を直す

## 4. そのほかの画面の確認
- [x] AdSense: 審査の状態と、ads.txt に警告が出ていないかを見て、記録欄に書く
- [ ] GoatCounter（https://kaitoinoue.goatcounter.com）: `/items/` で始まるページの訪問数を週に1回、記録欄に書く

## 5. 人がやること（Claude には頼めない）
- [ ] コミルの土曜の質問を記録する。名前は書かず、1行に「日付・学年・科目・単元・質問の要旨・どこでつまずいたか」。たまったら、クラウドの Claude に貼って「パターン集を作って」と頼む
- [ ] コミルの契約で、自分で作った教材の扱いと副業の決まりを確認する
- [ ] 卒業後（義務年限中）にサイトの広告収入を続けてよいか、県の担当に確認する

## 記録欄
| 日付 | 登録済みページ数 | 表示回数（28日） | クリック（28日） | AdSense | メモ |
|---|---|---|---|---|---|
| 2026-10-23 | （未確認） | 3か月で34 | 3か月で11 | 再審査待ち | 930ページ化の前 |
| 2026-10-23 | （未確認） | — | — | 要確認（有用性の低いコンテンツ）・ads.txt承認済み | 930ページ化を公開、sitemap再送信済み・検出数と処理状況は数日後に確認、URL検査8件リクエスト |
