const root = document.querySelector('.physics-tools');
const queryBox = root.querySelector('input[type="search"]');
const must = root.querySelector('input[type="checkbox"]');
const chapter = root.querySelector('select');
const counter = root.querySelector('output');
const supplement = {
  'ph-kinem-3eq.html':'等加速度 3公式 v=v0+at v=v₀+at',
  'ph-motion-law.html':'運動方程式 f=ma Σf=ma',
  'ph-energy-cons.html':'力学的エネルギー保存 保存則 k+u',
  'ph-circuit-ohm.html':'オームの法則 v=ri r=v/i',
  'ph-thermo-calor.html':'熱量 比熱 熱容量 q=mcΔt',
  'ph-wave-eq.html':'波の基本式 v=fλ 波長 振動数 周波数',
  'ph-kinem-vt.html':'vt v-t グラフ 傾き',
  'ph-circuit-power.html':'電力 ジュール熱 vi i2r w=pt',
  'ph-force-fric.html':'摩擦係数 μ 静止摩擦 動摩擦'
};
const normalize = text => text.normalize('NFKC').toLowerCase().replace(/\s+/g,'');
const outline = [...document.querySelectorAll('main.ilist > h2[id]')].map(heading => {
  const list = heading.nextElementSibling;
  const items = [...list.children].filter(el => el.tagName === 'LI').map(node => {
    const href = node.querySelector('a')?.getAttribute('href');
    return {node, text:normalize(heading.textContent + ' ' + node.textContent + ' ' + (supplement[href] || '')),
            must:!!node.querySelector('.tier-mini.must')};
  });
  chapter.add(new Option(heading.textContent,heading.id));
  return {heading,list,items};
});
function update() {
  const tokens = queryBox.value.trim().split(/[\s　]+/).map(normalize).filter(Boolean);
  const active = must.checked || tokens.length > 0;
  document.querySelectorAll('main.ilist > .grp').forEach(el => {el.hidden = active;});
  let total = 0;
  for (const {heading,list,items} of outline) {
    let count = 0;
    for (const item of items) {
      const match = (!must.checked || item.must) && tokens.every(token => item.text.includes(token));
      item.node.hidden = !match;
      count += Number(match);
    }
    heading.hidden = count === 0;
    list.hidden = count === 0;
    total += count;
  }
  counter.textContent = total ? total + '項目' : '該当する項目がありません。';
}
root.querySelector('.physics-controls').hidden = false;
queryBox.addEventListener('input',update);
must.addEventListener('change',update);
chapter.addEventListener('change',() => {
  const target = document.getElementById(chapter.value);
  if (!target) return;
  queryBox.value = '';
  must.checked = false;
  update();
  target.setAttribute('tabindex','-1');
  target.focus({preventScroll:true});
  target.scrollIntoView();
});
update();
