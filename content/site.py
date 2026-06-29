# 사이트 공통 설정
BASE_URL = "https://seodaemun-massage.netlify.app"

BRAND = "간다 GO"
PHONE = "0508-202-4719"
PHONE_DISPLAY = "0508-202-4719"

# 네이버 서치어드바이저 사이트 소유확인 코드 (메인 페이지 head에 출력)
NAVER_VERIFY = "7fef544e5a7d594f2f2c76f1c34c1c79210e50ed"

# 후기 기반 평점(스키마 AggregateRating) — 실제 게재 후기 수와 평균 점수
RATING_VALUE = "4.9"
RATING_COUNT = 7

# 상단 메뉴 — 하위 메뉴에는 키워드를 반복하지 않고 지역명·역명만 표시한다.
NAV = [
    ("홈", "/", []),
    ("서대문 출장마사지", "/massage/", [
        ("출장마사지 안내", "/massage/#service"),
        ("홈타이 안내", "/massage/#hometai"),
        ("전지역 방문 안내", "/massage/#coverage"),
        ("지하철역 인근 안내", "/massage/#stations"),
        ("예약 가능 시간", "/massage/#hours"),
        ("코스 선택 안내", "/massage/#course"),
        ("이용 전 확인사항", "/massage/#check"),
        ("위생·안전 안내", "/massage/#safety"),
        ("자주 묻는 질문", "/massage/#faq"),
    ]),
    ("지역별 안내", "/seodaemun-gu/", [
        ("서대문구 전체", "/seodaemun-gu/"),
        ("충현동", "/seodaemun-gu/chunghyeon-dong/"),
        ("천연동", "/seodaemun-gu/cheonyeon-dong/"),
        ("북아현동", "/seodaemun-gu/bugahyeon-dong/"),
        ("신촌동", "/seodaemun-gu/sinchon-dong/"),
        ("연희동", "/seodaemun-gu/yeonhui-dong/"),
        ("홍제동", "/seodaemun-gu/hongje-dong/"),
        ("홍은동", "/seodaemun-gu/hongeun-dong/"),
        ("남가좌동", "/seodaemun-gu/namgajwa-dong/"),
        ("북가좌동", "/seodaemun-gu/bukgajwa-dong/"),
    ]),
    ("지하철역별 안내", "/seodaemun-gu/stations/", [
        ("역 전체", "/seodaemun-gu/stations/"),
        ("신촌역", "/seodaemun-gu/stations/sinchon-station/"),
        ("이대역", "/seodaemun-gu/stations/ewha-womans-univ-station/"),
        ("아현역", "/seodaemun-gu/stations/ahyeon-station/"),
        ("충정로역", "/seodaemun-gu/stations/chungjeongno-station/"),
        ("홍제역", "/seodaemun-gu/stations/hongje-station/"),
        ("무악재역", "/seodaemun-gu/stations/muakjae-station/"),
        ("독립문역", "/seodaemun-gu/stations/dongnimmun-station/"),
        ("서대문역", "/seodaemun-gu/stations/seodaemun-station/"),
        ("가좌역", "/seodaemun-gu/stations/gajwa-station/"),
    ]),
    ("테마별 안내", "/themes/", [
        ("전체 테마", "/themes/"),
        ("스웨디시", "/themes/swedish/"),
        ("로미로미", "/themes/lomilomi/"),
        ("타이마사지", "/themes/thai/"),
        ("중국마사지", "/themes/chinese/"),
        ("아로마테라피", "/themes/aroma/"),
        ("홈케어", "/themes/homecare/"),
        ("호텔식마사지", "/themes/hotel-style/"),
        ("발마사지", "/themes/foot/"),
        ("스포츠·경락", "/themes/sports/"),
        ("스킨케어", "/themes/skincare/"),
        ("왁싱", "/themes/waxing/"),
        ("커플 관리", "/themes/couple/"),
        ("24시간", "/themes/24hours/"),
        ("수면 가능", "/themes/overnight/"),
    ]),
    ("코스안내", "/courses/", [
        ("전체 코스", "/courses/"),
        ("피로 회복 관리", "/courses/#recovery"),
        ("아로마 관리", "/courses/#aroma"),
        ("스포츠 관리", "/courses/#sports"),
        ("홈타이 코스", "/courses/#hometai"),
        ("커플·가족 방문 관리", "/courses/#couple"),
        ("기업·단체 방문 관리", "/courses/#group"),
        ("가격 안내", "/courses/#price"),
        ("코스 선택 가이드", "/courses/#guide"),
    ]),
    ("예약안내", "/reservation/", [
        ("예약 방법", "/reservation/#how"),
        ("예약 가능 시간", "/reservation/#hours"),
        ("방문 가능 장소", "/reservation/#place"),
        ("결제 안내", "/reservation/#payment"),
        ("변경·취소 안내", "/reservation/#change"),
        ("예약 전 체크사항", "/reservation/#check"),
    ]),
    ("이용가이드", "/guide/", [
        ("처음 이용하시는 분", "/guide/#first"),
        ("방문 전 준비사항", "/guide/#prepare"),
        ("위생 및 안전 기준", "/guide/#hygiene"),
        ("관리 후 주의사항", "/guide/#after"),
        ("금지행위 안내", "/guide/#prohibited"),
        ("이용 FAQ", "/guide/#faq"),
    ]),
    ("매거진", "/magazine/", [
        ("전체 글", "/magazine/"),
        ("마사지 비교 가이드", "/magazine/swedish-vs-thai/"),
        ("처음 이용 가이드", "/magazine/first-time-guide/"),
        ("수면과 마사지", "/magazine/sleep-and-massage/"),
        ("운동 후 회복", "/magazine/post-workout-timing/"),
        ("어깨·목 결림 관리", "/magazine/neck-shoulder-care/"),
        ("부모님 선물 가이드", "/magazine/parents-gift/"),
    ]),
    ("후기", "/reviews/", [
        ("전체 후기", "/reviews/"),
        ("지역별 후기", "/reviews/#area"),
        ("역세권 후기", "/reviews/#station"),
        ("후기 작성 안내", "/reviews/#write"),
    ]),
    ("고객센터", "/support/", [
        ("공지사항", "/support/#notice"),
        ("자주 묻는 질문", "/support/#faq"),
        ("1:1 문의", "/support/#contact"),
        ("제휴·기업 문의", "/support/#biz"),
        ("개인정보처리방침", "/support/privacy/"),
        ("이용약관", "/support/terms/"),
    ]),
]
