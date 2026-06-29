#!/usr/bin/env python3
"""검색엔진 즉시 색인 통보 스크립트 — 간다 GO (seodaemun-massage.netlify.app)

기능:
  1. IndexNow  — 빙(Bing)·네이버 등 IndexNow 참여 엔진에 URL 변경 즉시 통보
  2. Google Indexing API — 구글은 IndexNow 미참여이므로 별도 API 사용 (선택)
  3. sitemap 재제출 안내 — 구글·빙의 sitemap ping 엔드포인트는 2023~2024년에
     폐기되어(404 반환) 더 이상 동작하지 않는다. 대신 IndexNow와 서치콘솔
     등록 sitemap의 lastmod 갱신으로 대체한다.

사용법:
  python3 scripts/notify_search.py                  # sitemap.xml의 전체 URL 통보
  python3 scripts/notify_search.py URL [URL ...]    # 지정 URL만 통보
  python3 scripts/notify_search.py --changed A.html B.html
                                                    # 변경된 index.html 경로를 URL로 변환해 통보

Google Indexing API를 쓰려면 (선택):
  - GCP 서비스 계정 생성 → Web Search Indexing API 활성화
  - 서치콘솔 속성에 서비스 계정 이메일을 '소유자'로 추가
  - 환경변수 GOOGLE_SERVICE_ACCOUNT_FILE=서비스계정.json 경로 지정
  - pip install google-auth requests
"""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from content.site import BASE_URL  # noqa: E402

HOST = BASE_URL.split("//", 1)[1].rstrip("/")
INDEXNOW_KEY = "e19c7f43afd7c0ee0f2f0e305abadecd"
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",          # 공용 (참여 엔진 전체 전파)
    "https://www.bing.com/indexnow",              # 빙 직접
    "https://searchadvisor.naver.com/indexnow",   # 네이버 직접
]
GOOGLE_SCOPE = "https://www.googleapis.com/auth/indexing"
GOOGLE_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def sitemap_urls() -> list:
    tree = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in tree.findall(".//sm:loc", ns)]


def paths_to_urls(paths) -> list:
    urls = []
    for p in paths:
        p = p.replace("\\", "/").lstrip("./")
        if not p.endswith("index.html"):
            continue
        rel = p[: -len("index.html")]
        urls.append(BASE_URL.rstrip("/") + "/" + rel)
    return urls


def submit_indexnow(urls) -> None:
    payload = json.dumps({
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{BASE_URL.rstrip('/')}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }).encode("utf-8")
    for endpoint in INDEXNOW_ENDPOINTS:
        req = urllib.request.Request(
            endpoint, data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                print(f"[IndexNow] {endpoint} → HTTP {res.status}")
        except Exception as e:  # 4xx/5xx 포함
            print(f"[IndexNow] {endpoint} → 실패: {e}")


def submit_google(urls) -> None:
    cred_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    if not cred_file or not os.path.exists(cred_file):
        print("[Google] GOOGLE_SERVICE_ACCOUNT_FILE 미설정 — Indexing API 통보 건너뜀")
        return
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests
    except ImportError:
        print("[Google] google-auth 미설치 — `pip install google-auth requests` 후 재실행")
        return
    creds = service_account.Credentials.from_service_account_file(
        cred_file, scopes=[GOOGLE_SCOPE])
    creds.refresh(google.auth.transport.requests.Request())
    for url in urls:
        body = json.dumps({"url": url, "type": "URL_UPDATED"}).encode("utf-8")
        req = urllib.request.Request(
            GOOGLE_ENDPOINT, data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds.token}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                print(f"[Google] {url} → HTTP {res.status}")
        except Exception as e:
            print(f"[Google] {url} → 실패: {e}")


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--changed":
        urls = paths_to_urls(args[1:])
    elif args:
        urls = args
    else:
        urls = sitemap_urls()
    urls = sorted(set(urls))
    if not urls:
        print("통보할 URL이 없습니다.")
        return
    print(f"{len(urls)}개 URL 통보:")
    for u in urls:
        print(" -", u)
    submit_indexnow(urls)
    submit_google(urls)


if __name__ == "__main__":
    main()
