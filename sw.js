// 오프라인용 — 네트워크 우선, 끊기면 캐시
// 🔴 GitHub Pages 는 파일마다 `Cache-Control: max-age=600` 을 붙인다 → 그냥 fetch 하면 고친 판이 최대 10분 늦게 뜬다(10-13).
//    같은 사이트 파일은 cache:'no-cache' 로 «바뀌었나» 를 서버에 매번 확인(안 바뀌었으면 304 로 짧게 끝남).
const CACHE = 'shiftcal-v5';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png', 'holidays.json', 'extras.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES.map(f => new Request(f, { cache: 'no-cache' })))));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const same = new URL(e.request.url).origin === self.location.origin;
  // 화면 이동(navigate) 요청은 init 을 붙여 복제할 수 없어 주소로 새로 만든다
  const req = !same ? e.request
    : e.request.mode === 'navigate' ? new Request(e.request.url, { cache: 'no-cache', credentials: 'same-origin' })
    : new Request(e.request, { cache: 'no-cache' });
  e.respondWith(
    fetch(req)
      .then(r => { if (r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); } return r; })
      .catch(() => caches.match(e.request).then(r => r || caches.match('index.html')))
  );
});
