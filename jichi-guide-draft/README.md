# 自治医大まわりの手帖

自治医科大学の学生向けの読み物サイト（勉強する場所・食べる場所）。静的ファイルで、ビルドは `python3 build.py`。

- `data/study.json` 勉強スポット（親サイトの study-map のデータから、自治医大の直線20km以内を抜き出したもの）。`"visited": true` を足すと「筆者が行った」の印
- `data/eat.json` 食べる場所。実際に行った店だけを足す。空のあいだ、食べるページは noindex
- 公開先: GitHub Pages（このフォルダの中身をリポジトリの直下に置く）。手順は親リポジトリの `.claude/local-tasks.md` の 6-3
