// 併願・遠征プランナーのデータ。直すのはここだけ。
// dates: 一次試験の日。複数あれば「出願時に選べる」ものとして扱う（選べるかどうかが不明なものは note に書く）
// status: 'ok' は大学の募集要項で確認したもの。'wait' は予備校などのまとめで見ただけで、募集要項は未確認
// region: 移動の目安に使う地域。city: 宿を探すときの地名（大学の所在地）
var HEIGAN_CHECKED = '2026-10-25';
var HEIGAN_YEAR = '2027年度入試';

// 宿の予約サイトの紹介リンク。提携サービスに登録したら、そのリンクの形をここに入れる。
// {q}=検索語 {checkin}=チェックイン日(YYYY-MM-DD) {checkout}=チェックアウト日。空のうちは Google 検索へのふつうのリンクになり、広告表示も出ない。
// ※ 使いはじめるときは about/index.html の「収益について」にある「特定の商品やサービスを推奨して対価を受け取ることもしていません」を直すこと。
var HOTEL_LINK_TEMPLATE = '';

var REGIONS = ['北海道・東北', '関東', '中部・北陸', '関西', '中国・四国', '九州・沖縄'];

var HEIGAN_SCHOOLS = [
  {id:'teikyo', name:'帝京大学', city:'東京都板橋区', region:'関東', dates:['2027-01-21','2027-01-22','2027-01-23'], status:'wait', note:'1月21〜23日のうち選べるとするまとめが多い'},
  {id:'iuhw', name:'国際医療福祉大学', city:'千葉県成田市', region:'関東', dates:['2027-01-25'], status:'wait', note:'自治医科大学の学力試験と同じ日'},
  {id:'kindai', name:'近畿大学（前期）', city:'大阪府大阪狭山市', region:'関西', dates:['2027-01-31'], status:'wait'},
  {id:'kawasaki', name:'川崎医科大学', city:'岡山県倉敷市', region:'中国・四国', dates:['2027-02-01'], status:'wait', note:'出願は2026年12月1日〜2027年1月7日17時必着とするまとめあり'},
  {id:'nihon', name:'日本大学（N方式第1期）', city:'東京都板橋区', region:'関東', dates:['2027-02-01'], status:'wait'},
  {id:'kurume', name:'久留米大学（前期）', city:'福岡県久留米市', region:'九州・沖縄', dates:['2027-02-01'], status:'wait'},
  {id:'twmu', name:'東京女子医科大学', city:'東京都新宿区', region:'関東', dates:['2027-02-01'], status:'wait'},
  {id:'nms', name:'日本医科大学（前期）', city:'東京都文京区', region:'関東', dates:['2027-02-01'], status:'wait'},
  {id:'kyorin', name:'杏林大学', city:'東京都三鷹市', region:'関東', dates:['2027-02-02'], status:'wait'},
  {id:'kmu', name:'関西医科大学（前期）', city:'大阪府枚方市', region:'関西', dates:['2027-02-02'], status:'wait'},
  {id:'tokai', name:'東海大学', city:'神奈川県伊勢原市', region:'関東', dates:['2027-02-02','2027-02-03'], status:'wait', note:'選べるとするまとめがある。地域枠・共テ利用は日程が別'},
  {id:'fukuoka', name:'福岡大学', city:'福岡県福岡市', region:'九州・沖縄', dates:['2027-02-02'], status:'wait'},
  {id:'kitasato', name:'北里大学', city:'神奈川県相模原市', region:'関東', dates:['2027-02-02'], status:'wait'},
  {id:'kanazawa', name:'金沢医科大学（前期）', city:'石川県河北郡内灘町', region:'中部・北陸', dates:['2027-02-03','2027-02-04'], status:'wait', note:'出願時に選べるとするまとめがある'},
  {id:'juntendo', name:'順天堂大学（A・B方式）', city:'東京都文京区', region:'関東', dates:['2027-02-03'], status:'wait'},
  {id:'iwate', name:'岩手医科大学', city:'岩手県紫波郡矢巾町', region:'北海道・東北', dates:['2027-02-03'], status:'wait'},
  {id:'tohoku-mpu', name:'東北医科薬科大学', city:'宮城県仙台市', region:'北海道・東北', dates:['2027-02-04'], status:'wait', note:'二次試験の日を大学が指定する形（2月20日か21日とするまとめあり）'},
  {id:'fujita', name:'藤田医科大学', city:'愛知県豊明市', region:'中部・北陸', dates:['2027-02-04'], status:'wait'},
  {id:'stmarianna', name:'聖マリアンナ医科大学（前期）', city:'神奈川県川崎市', region:'関東', dates:['2027-02-04'], status:'wait', note:'出願時に日を選べるとするまとめがあるが、ほかの日は確認できていない'},
  {id:'saitama', name:'埼玉医科大学（前期）', city:'埼玉県入間郡毛呂山町', region:'関東', dates:['2027-02-04'], status:'wait'},
  {id:'hyogo', name:'兵庫医科大学', city:'兵庫県西宮市', region:'関西', dates:['2027-02-04'], status:'wait', note:'2月4日とするまとめが多いが、年度で動いている'},
  {id:'showa', name:'昭和医科大学（Ⅰ期）', city:'東京都品川区', region:'関東', dates:['2027-02-05'], status:'wait'},
  {id:'tokyo-med', name:'東京医科大学', city:'東京都新宿区', region:'関東', dates:['2027-02-06'], status:'wait'},
  {id:'toho', name:'東邦大学', city:'東京都大田区', region:'関東', dates:['2027-02-07'], status:'wait'},
  {id:'keio', name:'慶應義塾大学', city:'東京都新宿区', region:'関東', dates:['2027-02-09'], status:'wait', note:'2月9日とするのは1つのまとめのみ'},
  {id:'aichi', name:'愛知医科大学', city:'愛知県長久手市', region:'中部・北陸', dates:['2027-02-09'], status:'ok', note:'2027年度の学生募集要項で、第1次試験は2月9日（火）'},
  {id:'ompu', name:'大阪医科薬科大学', city:'大阪府高槻市', region:'関西', dates:['2027-02-10'], status:'wait'},
  {id:'jikei', name:'東京慈恵会医科大学', city:'東京都港区', region:'関東', dates:['2027-02-11'], status:'wait', note:'日本大学の二次試験と同じ日とするまとめあり'},
  {id:'uoeh', name:'産業医科大学（A方式）', city:'福岡県北九州市', region:'九州・沖縄', dates:['2027-02-14'], status:'wait', note:'トップページの日程表と同じ。国公立の出願前の時期'}
];

var HEIGAN_SOURCES = [
  ['愛知医科大学 医学部 令和9(2027)年度 学生募集要項（公式PDF）', 'https://www.aichi-med-u.ac.jp/files/igaku/2027nenndogakuseibosyuuyoukou_0731.pdf'],
  ['2027年度 私立医学部入試日程一覧（四谷学院）', 'https://www.yotsuyagakuin.com/b_geneki/igakubu-schedule/'],
  ['2027年度 私立医学部入試・出願カレンダー（YMS）', 'https://yms.ne.jp/calender/'],
  ['【2027年度】私立医学部入試日程一覧と併願戦略（医学部ラボ）', 'https://www.medical-labo.com/labo-tsushin/labo-tsushin-61042/'],
  ['2027年度最新カレンダー 私立医学部入試の日程一覧（スタディカルテ、2026年7月30日更新）', 'https://studykartelab.com/news-posts/private_examschedule2027'],
  ['2027年度 私立医学部入試・出願締切カレンダー（メビオ）', 'https://www.mebio.co.jp/medicalschool/calendar/'],
  ['2027年度 私立医学部入試で2月2日・2月4日に大学が集中（代官山メディカル）', 'https://daikanyamamedical.com/blog/2026/06/08/0608/']
];
