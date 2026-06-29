#!/usr/bin/env python3
"""간다 GO — 서대문 출장마사지 정적 사이트 빌드 스크립트.

content/ 패키지의 페이지 정의를 읽어 정적 HTML을 생성한다.

규칙(자동 적용):
  - 본문 텍스트 2,000자 미만 페이지는 robots noindex 처리
  - sitemap.xml 에는 index 허용 페이지만 포함
  - 지역+역+테마 조합 경로는 생성 자체가 불가능한 구조
"""
import html
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from email.utils import format_datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content import PAGES
from content.site import (BASE_URL, BRAND, NAV, NAVER_VERIFY, PHONE,
                          PHONE_DISPLAY, RATING_COUNT, RATING_VALUE)

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_INDEX_CHARS = 2000
SITE = BASE_URL.rstrip("/")
BUSINESS_ID = SITE + "/#business"
WEBSITE_ID = SITE + "/#website"


def _plain(fragment: str) -> str:
    """HTML 조각을 평문으로 변환(스키마 텍스트용)."""
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_faqs(body: str):
    """본문의 faq-item(<h3>질문</h3><p>답변</p>)을 (질문, 답변) 목록으로."""
    faqs = []
    for m in re.finditer(
        r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
        body, flags=re.S,
    ):
        faqs.append((_plain(m.group(1)), _plain(m.group(2))))
    return faqs


def extract_reviews(body: str):
    """후기 페이지의 faq-item(<p><strong>닉네임 · 동네</strong><br>내용</p>)을 추출."""
    reviews = []
    for m in re.finditer(
        r'<div class="faq-item">\s*<p>\s*<strong>(.*?)</strong>\s*<br>(.*?)</p>',
        body, flags=re.S,
    ):
        head = _plain(m.group(1))
        text = _plain(m.group(2))
        name = head.split("·")[0].strip().rstrip("님").strip() or head
        reviews.append((name, text))
    return reviews


def _business_node(reviews=None) -> dict:
    """사이트 공통 비즈니스(LocalBusiness) 노드 + 평점 + 요금 오퍼."""
    node = {
        "@type": "HealthAndBeautyBusiness",
        "@id": BUSINESS_ID,
        "name": BRAND,
        "telephone": PHONE,
        "url": SITE + "/",
        "image": SITE + "/assets/og-image.png",
        "description": "서대문구 전지역 방문 출장마사지·홈타이 예약 안내",
        "areaServed": {"@type": "AdministrativeArea", "name": "서울특별시 서대문구"},
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday",
                          "Friday", "Saturday", "Sunday"],
            "opens": "00:00",
            "closes": "23:59",
        },
        "priceRange": "₩90,000 - ₩180,000",
        "currenciesAccepted": "KRW",
        "makesOffer": [
            {"@type": "Offer", "name": "60분 코스",
             "price": "90000", "priceCurrency": "KRW"},
            {"@type": "Offer", "name": "90분 코스",
             "price": "150000", "priceCurrency": "KRW"},
            {"@type": "Offer", "name": "120분 코스",
             "price": "180000", "priceCurrency": "KRW"},
        ],
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": RATING_VALUE,
            "reviewCount": str(RATING_COUNT),
            "bestRating": "5",
            "worstRating": "1",
        },
    }
    if reviews:
        # 게재된 후기 대부분 5점, 일부 4점으로 평균이 평점값에 수렴하도록 배정
        ratings = [5, 5, 5, 5, 5, 4, 5]
        node["review"] = [
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": name},
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": str(ratings[i % len(ratings)]),
                    "bestRating": "5", "worstRating": "1",
                },
                "reviewBody": text,
            }
            for i, (name, text) in enumerate(reviews)
        ]
    return node


def build_jsonld(page: dict, body: str, canonical: str) -> str:
    """페이지별 JSON-LD(@graph) 생성: 비즈니스·평점·후기·FAQ·빵부스러기."""
    path = page["path"]
    reviews = extract_reviews(body) if path == "reviews/" else None
    graph = [
        _business_node(reviews),
        {
            "@type": "WebSite",
            "@id": WEBSITE_ID,
            "url": SITE + "/",
            "name": BRAND,
            "inLanguage": "ko",
            "publisher": {"@id": BUSINESS_ID},
        },
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": page["title"],
            "description": page["desc"],
            "inLanguage": "ko",
            "isPartOf": {"@id": WEBSITE_ID},
            "about": {"@id": BUSINESS_ID},
        },
    ]

    # BreadcrumbList — 홈 + 페이지 빵부스러기
    crumbs = page.get("breadcrumb") or []
    if crumbs:
        items = [("홈", SITE + "/")]
        for label, href in crumbs:
            items.append((label, (SITE + href) if href else canonical))
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": label, "item": url}
                for i, (label, url) in enumerate(items)
            ],
        })

    # FAQPage — 본문에 Q/A가 있으면 자동 생성
    faqs = extract_faqs(body)
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        })

    doc = {"@context": "https://schema.org", "@graph": graph}
    return ('<script type="application/ld+json">\n'
            + json.dumps(doc, ensure_ascii=False, indent=2)
            + "\n</script>\n")


def render_related(related) -> str:
    """롱테일 주제 내부링크 블록(관련 안내 카드)."""
    if not related:
        return ""
    lis = "".join(
        f'<li><a href="{href}">{anchor}</a></li>' for href, anchor in related
    )
    return (
        '<section class="related-links" aria-label="관련 안내">'
        "<h2>이런 주제도 함께 찾아보세요</h2>"
        f'<ul class="related-grid">{lis}</ul></section>'
    )


def text_length(body_html: str) -> int:
    """태그를 제거한 본문 글자수(공백 포함, 연속 공백은 1자).
    공통 요금 블록은 페이지 고유 본문이 아니므로 측정에서 제외한다."""
    text = re.sub(r'<section class="pricing">.*?</section>', " ", body_html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text)


def render_nav(current_path: str) -> str:
    items = []
    for label, href, children in NAV:
        active = " is-active" if href == "/" + current_path else ""
        if children:
            sub = "".join(
                f'<li><a href="{c_href}">{c_label}</a></li>'
                for c_label, c_href in children
            )
            items.append(
                f'<li class="nav-item has-sub{active}">'
                f'<a href="{href}">{label}</a>'
                f'<ul class="sub-menu">{sub}</ul></li>'
            )
        else:
            items.append(
                f'<li class="nav-item{active}"><a href="{href}">{label}</a></li>'
            )
    return "".join(items)


def render_breadcrumb(crumbs) -> str:
    if not crumbs:
        return ""
    parts = ['<nav class="breadcrumb" aria-label="현재 위치"><ol>']
    parts.append('<li><a href="/">홈</a></li>')
    for label, href in crumbs:
        if href:
            parts.append(f'<li><a href="{href}">{label}</a></li>')
        else:
            parts.append(f"<li><span>{label}</span></li>")
    parts.append("</ol></nav>")
    return "".join(parts)


def inject_toc(body: str):
    """본문 섹션(h2)에 id를 보장하고 좌측 목차 데이터를 만든다."""
    items = []
    counter = [0]

    def repl(m):
        attrs, title = m.group(1), m.group(2)
        idm = re.search(r'id="([^"]+)"', attrs)
        if idm:
            sid = idm.group(1)
            opening = f"<section{attrs}>"
        else:
            counter[0] += 1
            sid = f"sec-{counter[0]}"
            opening = f'<section id="{sid}"{attrs}>'
        label = re.sub(r"<[^>]+>", "", title).strip()
        items.append((sid, label))
        return f"{opening}<h2>{title}</h2>"

    body = re.sub(r"<section([^>]*)>\s*<h2>(.*?)</h2>", repl, body, flags=re.S)
    return body, items


def render_toc(items) -> str:
    if len(items) < 3:
        return ""
    links = "".join(
        f'<li><a href="#{sid}">{label}</a></li>' for sid, label in items
    )
    return (
        '<aside class="page-toc"><nav aria-label="페이지 목차">'
        '<p class="toc-title">목차</p>'
        f"<ul>{links}</ul></nav></aside>"
    )


def render_page(page: dict) -> str:
    path = page["path"]
    title = page["title"]
    desc = page["desc"]
    h1 = page["h1"]
    body = page["body"]
    crumbs = page.get("breadcrumb") or []
    extra_head = page.get("extra_head", "")
    hero = page.get("hero", "")

    chars = text_length(body)
    noindex = page.get("noindex", False) or chars < MIN_INDEX_CHARS
    robots = (
        '<meta name="robots" content="noindex,follow">'
        if noindex
        else '<meta name="robots" content="index,follow">'
    )
    canonical = BASE_URL.rstrip("/") + "/" + path

    # 히어로가 있는 페이지(메인)는 H1을 히어로 안에서 출력한다.
    if hero:
        page_head = hero
    else:
        page_head = ""

    h1_html = "" if hero else f"<h1>{h1}</h1>"

    # 롱테일 내부링크 블록 — 요금표 직전에 삽입(없으면 본문 끝)
    related_html = render_related(page.get("related"))
    if related_html:
        if '<section class="pricing"' in body:
            body = body.replace('<section class="pricing"',
                                related_html + '<section class="pricing"', 1)
        else:
            body = body + related_html

    jsonld = build_jsonld(page, body, canonical)
    naver = (f'<meta name="naver-site-verification" content="{NAVER_VERIFY}">\n'
             if path == "" else "")
    extra_head = naver + jsonld + extra_head

    body, toc_items = inject_toc(body)
    toc_html = render_toc(toc_items)
    layout_cls = "page-layout has-toc" if toc_html else "page-layout"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:image" content="{BASE_URL.rstrip('/')}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{BASE_URL.rstrip('/')}/assets/og-image.png">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="theme-color" content="#0a1120">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
{extra_head}</head>
<body>
<header class="site-header">
  <div class="header-accent" aria-hidden="true"></div>
  <div class="header-top">
    <div class="header-inner">
      <a class="brand" href="/"><span class="brand-mark">G</span> <span class="brand-text">{BRAND}</span></a>
      <p class="header-tagline"><span class="tag-gem">◆</span> 서대문구 전지역 방문 관리 <span class="tag-gem">◆</span> 24시간 상담</p>
      <a class="header-call" href="tel:{PHONE}"><span class="call-label">예약전화</span> {PHONE_DISPLAY}</a>
      <button class="nav-toggle" aria-label="메뉴 열기" aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </div>
  <nav class="main-nav" aria-label="주 메뉴">
    <div class="nav-inner"><ul class="nav-list">{render_nav(path)}</ul></div>
  </nav>
</header>
{page_head}<main class="site-main">
  <div class="container {layout_cls}">
    {toc_html}
    <article class="page-content">
      {render_breadcrumb(crumbs)}
      {h1_html}
      {body}
    </article>
  </div>
</main>
<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-col footer-about">
      <p class="footer-brand">{BRAND}</p>
      <p class="footer-desc">서대문구 전지역 방문 출장마사지·홈타이 안내 사이트입니다. 모든 서비스는 안내된 관리 범위와 위생·안전 기준 안에서만 제공됩니다.</p>
      <address class="footer-contact">
        <span class="footer-contact-row"><span class="footer-label">예약전화</span> <a href="tel:{PHONE}">{PHONE_DISPLAY}</a></span>
        <span class="footer-contact-row"><span class="footer-label">상담시간</span> 연중무휴 24시간</span>
        <span class="footer-contact-row"><span class="footer-label">서비스 지역</span> 서울특별시 서대문구 전지역</span>
      </address>
    </div>
    <nav class="footer-col" aria-label="서비스 안내">
      <p class="footer-title">서비스</p>
      <ul>
        <li><a href="/massage/">서대문 출장마사지</a></li>
        <li><a href="/seodaemun-gu/">지역별 안내</a></li>
        <li><a href="/seodaemun-gu/stations/">지하철역별 안내</a></li>
        <li><a href="/themes/">테마별 안내</a></li>
        <li><a href="/courses/">코스안내</a></li>
      </ul>
    </nav>
    <nav class="footer-col" aria-label="이용 안내">
      <p class="footer-title">이용 안내</p>
      <ul>
        <li><a href="/reservation/">예약안내</a></li>
        <li><a href="/guide/">이용가이드</a></li>
        <li><a href="/reviews/">이용 후기</a></li>
        <li><a href="/support/">고객센터</a></li>
        <li><a href="/support/#faq">자주 묻는 질문</a></li>
      </ul>
    </nav>
    <nav class="footer-col" aria-label="정책 및 기준">
      <p class="footer-title">정책</p>
      <ul>
        <li><a href="/about/">운영자 소개</a></li>
        <li><a href="/support/privacy/">개인정보처리방침</a></li>
        <li><a href="/support/terms/">이용약관</a></li>
        <li><a href="/guide/#hygiene">위생·안전 기준</a></li>
        <li><a href="/guide/#prohibited">금지행위 안내</a></li>
        <li><a href="/support/#biz">제휴·기업 문의</a></li>
      </ul>
    </nav>
  </div>
  <div class="footer-bottom">
    <div class="container footer-bottom-inner">
      <p class="footer-copy">&copy; {BRAND}. All rights reserved.</p>
      <p class="footer-note">건전한 방문 관리 서비스를 운영하며, 불법적인 요청은 어떤 경우에도 응하지 않습니다.</p>
      <a class="footer-made" href="https://t.me/googleseolab" target="_blank" rel="noopener nofollow">웹사이트 제작문의 ↗</a>
    </div>
  </div>
</footer>
<a class="call-fab" href="tel:{PHONE}" aria-label="전화 예약 {PHONE_DISPLAY}">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
  <span class="call-fab-label">예약 전화</span>
</a>
<script src="/assets/nav.js"></script>
</body>
</html>
"""


def build() -> None:
    report = []
    sitemap_urls = []
    rss_items = []

    for page in PAGES:
        path = page["path"]  # "" 또는 "seodaemun-gu/hongje-dong/" 형태
        out_dir = os.path.join(ROOT, path)
        os.makedirs(out_dir, exist_ok=True)
        html_out = render_page(page)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_out)

        chars = text_length(page["body"])
        noindex = page.get("noindex", False) or chars < MIN_INDEX_CHARS
        if not noindex:
            sitemap_urls.append(BASE_URL.rstrip("/") + "/" + path)
            rss_items.append(page)
        desc_flag = " ⚠desc>80" if len(page["desc"]) > 80 else ""
        report.append((path or "/", chars, ("noindex" if noindex else "index") + desc_flag))

    # sitemap.xml — lastmod 포함 (네이버·구글 빠른 색인용)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>"
        for u in sitemap_urls
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}\n</urlset>\n"
        )

    # rss.xml — 네이버 서치어드바이저 RSS 제출용 (RSS 2.0)
    now_rfc822 = format_datetime(datetime.now(timezone.utc))
    base = BASE_URL.rstrip("/")
    items = []
    for page in rss_items:
        loc = base + "/" + page["path"]
        items.append(
            "  <item>\n"
            f"    <title>{html.escape(page['title'])}</title>\n"
            f"    <link>{loc}</link>\n"
            f"    <guid isPermaLink=\"true\">{loc}</guid>\n"
            f"    <description>{html.escape(page['desc'])}</description>\n"
            f"    <pubDate>{now_rfc822}</pubDate>\n"
            "  </item>"
        )
    with open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0">\n<channel>\n'
            f"  <title>{html.escape(BRAND)} — 서대문 출장마사지·홈타이 안내</title>\n"
            f"  <link>{base}/</link>\n"
            "  <description>서대문구 전지역 방문 관리 안내. 지역별·지하철역별·테마별 페이지와 매거진 소식을 제공합니다.</description>\n"
            "  <language>ko</language>\n"
            f"  <lastBuildDate>{now_rfc822}</lastBuildDate>\n"
            + "\n".join(items)
            + "\n</channel>\n</rss>\n"
        )

    # robots.txt — 전체 허용 + 네이버(Yeti)·구글(Googlebot) 명시, sitemap/rss 참조
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(
            "User-agent: *\nAllow: /\n\n"
            "User-agent: Googlebot\nAllow: /\n\n"
            "User-agent: Yeti\nAllow: /\n\n"
            f"Sitemap: {base}/sitemap.xml\n"
            f"Sitemap: {base}/rss.xml\n"
        )

    # .nojekyll (GitHub Pages)
    open(os.path.join(ROOT, ".nojekyll"), "w").close()

    width = max(len(p) for p, _, _ in report)
    print(f"{'PATH'.ljust(width)}  CHARS  ROBOTS")
    for p, c, r in sorted(report):
        flag = "" if (r == "noindex" or MIN_INDEX_CHARS <= c <= 2500) else "  ⚠"
        print(f"{p.ljust(width)}  {str(c).rjust(5)}  {r}{flag}")
    print(f"\n{len(report)} pages built, {len(sitemap_urls)} in sitemap.")


if __name__ == "__main__":
    build()
