/* オフライン対応。アプリ本体は単一HTMLなので、初回アクセス後は通信なしで動く。
   ビルドのたびに CACHE の版が上がり、古いキャッシュは activate で捨てる。 */
const CACHE = 'todai-math-20260804-6vg9';
const ASSETS = [
  './', './index.html', './app.html', './manifest.webmanifest',
  './icon-192.png', './icon-512.png', './icon-maskable.png', './apple-touch-icon.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // ネットワーク優先・失敗したらキャッシュ（更新をすぐ反映しつつオフラインでも動く）
  e.respondWith(
    fetch(e.request)
      .then(r => {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        return r;
      })
      .catch(() => caches.match(e.request).then(r => r || caches.match('./app.html')))
  );
});
