// اسم الإصدار - غير الرقم ده لو عملت تحديث كبير
const CACHE_NAME = 'mall-togar-v1.0.0';

// الملفات اللي هتتخزن مؤقتاً عشان تشتغل بدون نت
const urlsToCache = [
  '/',
  '/index.html',
  '/my-store.html',
  '/sellers.html',
  '/product.html',
  '/upgrade.html',
  '/services.html',
  '/manifest.json'
];

// وقت تثبيت الـ Service Worker
self.addEventListener('install', event => {
  console.log('📦 Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('✅ تم تخزين الملفات مؤقتاً');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.error('❌ خطأ في التخزين:', err))
  );
  self.skipWaiting();
});

// وقت تنشيط الـ Service Worker
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('🗑️ حذف الإصدار القديم:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// وقت جلب الملفات (شغال بدون نت)
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // لو الملف موجود في الكاش، ارجعه
        if (response) {
          return response;
        }
        // لو مش موجود، جيبه من النت
        return fetch(event.request)
          .then(response => {
            // لو الاستجابة مش صالحة، ارجعها
            if (!response || response.status !== 200) {
              return response;
            }
            // خزن الملف الجديد في الكاش
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            return response;
          });
      })
  );
});