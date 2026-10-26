/* 目次：ページ上の一覧から、スクロール中に上に出る目次バーを作り、今読んでいる節を光らせる */
(function(){
  "use strict";
  var toc = document.querySelector('.toc');
  if (!toc || !('IntersectionObserver' in window)) return;
  var links = Array.prototype.slice.call(toc.querySelectorAll('a[href^="#"]'));
  var bar = document.createElement('nav');
  bar.className = 'toc-bar';
  bar.setAttribute('aria-label', 'ページ内の移動');
  var barLinks = {};
  links.forEach(function(a){
    var b = document.createElement('a');
    b.href = a.getAttribute('href');
    b.textContent = a.getAttribute('data-short') || a.textContent;
    bar.appendChild(b);
    barLinks[b.getAttribute('href').slice(1)] = b;
  });
  document.body.appendChild(bar);

  var hero = document.querySelector('.hero');
  if (hero){
    new IntersectionObserver(function(es){
      es.forEach(function(e){ bar.classList.toggle('show', !e.isIntersecting && e.boundingClientRect.top < 0); });
    }).observe(hero);
  }
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){
      if (!e.isIntersecting) return;
      Object.keys(barLinks).forEach(function(k){ barLinks[k].classList.toggle('on', k === e.target.id); });
      var on = barLinks[e.target.id];
      if (on) bar.scrollTo({ left: on.offsetLeft - 40, behavior: 'smooth' });
    });
  }, { rootMargin: '-35% 0px -60% 0px' });
  Object.keys(barLinks).forEach(function(id){ var t = document.getElementById(id); if (t) io.observe(t); });
})();
