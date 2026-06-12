// 모바일 내비게이션 토글
(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".main-nav");
  if (!toggle || !nav) return;

  toggle.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    toggle.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });

  // 모바일에서 1차 메뉴 탭 시 하위 메뉴 펼침
  nav.querySelectorAll(".nav-item.has-sub > a").forEach(function (link) {
    link.addEventListener("click", function (e) {
      if (window.innerWidth > 920) return;
      var item = link.parentElement;
      if (!item.classList.contains("sub-open")) {
        e.preventDefault();
        nav.querySelectorAll(".sub-open").forEach(function (el) {
          el.classList.remove("sub-open");
        });
        item.classList.add("sub-open");
      }
    });
  });
})();

// 좌측 목차 스크롤스파이 — 현재 읽는 섹션을 골드로 표시
(function () {
  var toc = document.querySelector(".page-toc");
  if (!toc || !("IntersectionObserver" in window)) return;

  var links = {};
  toc.querySelectorAll('a[href^="#"]').forEach(function (a) {
    links[a.getAttribute("href").slice(1)] = a;
  });

  var current = null;
  function activate(id) {
    if (current === id) return;
    current = id;
    toc.querySelectorAll("a.active").forEach(function (a) {
      a.classList.remove("active");
    });
    if (links[id]) links[id].classList.add("active");
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) activate(entry.target.id);
      });
    },
    { rootMargin: "-25% 0px -65% 0px", threshold: 0 }
  );

  Object.keys(links).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) observer.observe(el);
  });
})();
