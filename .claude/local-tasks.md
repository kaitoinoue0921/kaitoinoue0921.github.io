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
- [x] 「サイトマップ」で `sitemap.xml` を送信し直す。状態が「成功」になり、検出された URL が 1131 前後になることを確かめる
- [x] 「URL 検査」で次の URL を1つずつ入れ、「インデックス登録をリクエスト」を押す（1日の上限があるので、この順で入るところまで）
  1. https://kaitoinoue0921.github.io/juken/
  2. https://kaitoinoue0921.github.io/works/math-notes/items/
  3. https://kaitoinoue0921.github.io/works/chem-notes/items/
  4. https://kaitoinoue0921.github.io/works/physics-notes/items/
  5. https://kaitoinoue0921.github.io/works/eng-grammar-notes/items/
  6. 各ノートの `items/patterns.html`（4つ）
  7. https://kaitoinoue0921.github.io/todai-math-map/n/

## 3. Search Console（2〜3週間後）
- [ ] 「ページ」レポートで、登録済みのページ数と「検出 - インデックス未登録」の数を下の記録欄に書く
- [ ] 「検索パフォーマンス」→ 期間「28日間」→「ページ」タブを、表示回数の多い順に上位30件 CSV でエクスポートし、`.claude/gsc/YYYY-MM-DD-pages.csv` に保存してコミットする
  - 「クエリ」タブは書き出さない（このリポジトリは公開なので、ページ別の数字だけにする）
  - クラウドの Claude がこれを読んで、表示はあるのにクリックされないページのタイトルと説明文を直す

## 4. そのほかの画面の確認
- [ ] AdSense: 審査の状態と、ads.txt に警告が出ていないかを見て、記録欄に書く
- [ ] GoatCounter（https://kaitoinoue.goatcounter.com）: `/items/` で始まるページの訪問数を週に1回、記録欄に書く

## 5. 人がやること（Claude には頼めない）
- [ ] コミルの土曜の質問を記録する。名前は書かず、1行に「日付・学年・科目・単元・質問の要旨・どこでつまずいたか」。たまったら、クラウドの Claude に貼って「パターン集を作って」と頼む
- [ ] コミルの契約で、自分で作った教材の扱いと副業の決まりを確認する
- [ ] 卒業後（義務年限中）にサイトの広告収入を続けてよいか、県の担当に確認する

## 6. 併願プランナー・塾向けページ・自治医大サイト（2026-10-25 追加。ローカルの Chrome でやる）
クラウドからは予備校・大学のページに接続できず、ログインも要るため、ここに残す。ブランチは `claude/modest-hypatia-6e81uq`（main には未取り込み）。

### 6-1. 併願プランナーの日程を大学の募集要項で確かめる（最優先）
- [ ] `igakubu-roadmap/assets/heigan-data.js` の28校のうち、`status:'ok'`（募集要項で確認）は愛知医科大学だけ。残り27校の一次試験日を、各大学の2027年度の募集要項（公式サイト）で確かめる
- [ ] 合っていれば `status:'ok'` にして、`note` の「まとめで見ただけ」系の文を消す。違っていれば `dates` を直す
- [ ] とくに怪しいもの: 慶應（2/9は1つのまとめのみ）、兵庫医科（2/4か）、東海・金沢医科・聖マリアンナ・帝京（日を選べるか）、近畿（1/31 前期）、日本医科（前期/後期）、東北医科薬科（二次の日を大学が指定）
- [ ] 日程を確認できなかった大学（獨協医科、近畿の後期、日本医科の後期、埼玉医科の後期など）を足したければ足す
- [ ] 直したら `HEIGAN_CHECKED` の日付を更新してコミット

### 6-2. 楽天アフィリエイト（ログインが要る）
- [ ] https://affiliate.rakuten.co.jp/ にログインし、「リンク作成」などで出る `https://hb.afl.rakuten.co.jp/hgc/（ID）/` の（ID）を確かめる（ID の形は `xxxxxxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx`）
- [ ] `igakubu-roadmap/assets/heigan-data.js` の `RAKUTEN_AFFILIATE_ID` に入れる（ID は公開されても問題のない種類のもの。入れると、併願プランナーの「宿を探す」が「楽天トラベルで探す（広告）」になり、「広告を含みます」の表示も出る）
- [ ] 楽天トラベルのキーワード検索のURLを調べ、リンクが宿の検索ページに飛ぶようにしたい場合は、`heigan.html` の `hotelHref` の `https://travel.rakuten.co.jp/`（トップ）を検索URLに変える（クラウドでは検索URLの形を確かめられなかったため、いまはトップページ）
- [ ] **同時に** `about/index.html` の「収益について」の「特定の商品やサービスを推奨して対価を受け取ることもしていません」を、「宿泊予約サイトの紹介リンクから紹介料を受け取ることがあります」に直す（直さないと矛盾する）
- [ ] 楽天アフィリエイトの規約で、このサイトに載せてよいか（個人サイト・広告の表示方法・「広告を含みます」の表示）を確かめる
- [ ] 公開したら、リンクをクリックして楽天トラベルが開くこと、アフィリエイトの管理画面にクリックが記録されることを確かめる

### 6-3. 自治医大生向けサイト（別リポジトリ）
クラウドの権限ではリポジトリを作れなかった（403）。下書きは `jichi-guide-draft/`（`python3 build.py` で作り直せる静的サイト）。
- [ ] GitHub で `kaitoinoue0921/jichi-guide` を公開リポジトリとして作る（README なしの空でよい）
- [ ] `jichi-guide-draft/` の中身をそのリポジトリの直下に置いて main に push する（`.git` をこのリポジトリから持ち込まないこと）
- [ ] そのリポジトリの Settings → Pages → Source を「Deploy from a branch / main / (root)」にする。公開先は https://kaitoinoue0921.github.io/jichi-guide/
- [ ] 公開後、トップ・勉強する・食べる・このサイトについて の4ページが開くこと、勉強するページの絞り込みボタンが動くことを確かめる
- [ ] `ads.txt` は github.io のルートにある親サイトのものが効く。AdSense の管理画面で、このURLを追加のサイトとして出す必要があるかを確かめる
- [ ] Search Console に https://kaitoinoue0921.github.io/jichi-guide/ のサイトマップを送る（食べるページは中身ができるまで noindex）
- [ ] **店の情報を足す**: 実際に行った店だけ、`data/eat.json` に次の形で足して `python3 build.py`。`[{"name":"店名","genre":"ジャンル","area":"場所","price":"値段の目安","scene":"向いている時","visited":"2026-10","comment":"感想"}]`
- [ ] 実際に行った勉強場所は、`data/study.json` の該当の行に `"visited": true` を足すと「筆者が行った」の印が出る。「要確認」の項目も、行ったときに直す
- [ ] 公開するなら、親サイトからのリンク（`index.html` や `study-map/`）を足すかどうかを決める

## 記録欄
| 日付 | 登録済みページ数 | 表示回数（28日） | クリック（28日） | AdSense | メモ |
|---|---|---|---|---|---|
| 2026-10-23 | （未確認） | 3か月で34 | 3か月で11 | 再審査待ち | 930ページ化の前 |
| 2026-10-23（夕） | （未確認） | — | — | — | 1131ページ化をmainに取り込み公開（sitemap.xml は1131件を配信中）、サイトマップ再送信済み（送信直後で検出数は数日後に確認。画面上は直前の読み込みが「取得できませんでした」のまま）、URL検査は /juken/ を再リクエスト、残り7件は同日に8件リクエスト済みのため省略 |
| 2026-10-23（確認） | — | — | — | — | 公開確認: chem-notes/items/・ch-matter-pure.html・math-notes/items/patterns.html が200、化学式の描画エラーなし（.katex 10個、エラー0）。マージ済みで origin/main と一致 |
