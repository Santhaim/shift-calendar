# 구글 「대한민국의 휴일」 공개 달력(ICS) → holidays.json (웹앱이 읽는 공휴일 표)
#   py tools/fetch_holidays.py [출력경로=holidays.json]
# GitHub Actions 가 하루 한 번 돌려 바뀌었을 때만 커밋한다(.github/workflows/holidays.yml).
# 빨간 날/기념일 구분은 구글이 적어 주는 DESCRIPTION(「공휴일」/「기념일」)을 그대로 따른다.
import json, re, sys, urllib.request, datetime
from pathlib import Path

URL = "https://calendar.google.com/calendar/ical/ko.south_korea%23holiday%40group.v.calendar.google.com/public/basic.ics"


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "holidays.json")
    raw = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8")
    days = {}
    for ev in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", unfold(raw), re.S):
        f = {}
        for line in ev.strip().splitlines():
            k, _, v = line.partition(":")
            f[k.split(";")[0]] = v.strip()
        start = f.get("DTSTART", "")[:8]
        end = f.get("DTEND", "")[:8] or start
        title = f.get("SUMMARY", "").replace("\\,", ",").strip()
        if not (re.fullmatch(r"\d{8}", start) and title):
            continue
        red = f.get("DESCRIPTION", "").startswith("공휴일")
        if red and re.match(r"^쉬는\s*날", title):
            title = "대체공휴일"  # 구글의 「쉬는 날 개천절」 = 대체공휴일
        d = datetime.date(int(start[:4]), int(start[4:6]), int(start[6:]))
        e = datetime.date(int(end[:4]), int(end[4:6]), int(end[6:])) if re.fullmatch(r"\d{8}", end) else d
        while True:  # 종일 일정의 DTEND 는 «다음 날» — 그 전날까지
            k = d.isoformat()
            slot = days.setdefault(k, {"red": [], "other": []})
            arr = slot["red" if red else "other"]
            if title not in arr:
                arr.append(title)
            d += datetime.timedelta(days=1)
            if d >= e:
                break
    if len(days) < 50:
        raise SystemExit(f"공휴일이 너무 적다({len(days)}) — 원본이 바뀐 듯, 덮어쓰지 않음")
    data = {"source": "google:ko.south_korea#holiday", "days": dict(sorted(days.items()))}
    new = json.dumps(data, ensure_ascii=False, indent=1)
    if out.exists() and json.loads(out.read_text(encoding="utf-8")).get("days") == data["days"]:
        print("변경 없음", len(days))
        return
    out.write_text(new, encoding="utf-8", newline="\n")  # LF 고정(윈도우·리눅스 어디서 돌려도 같은 파일)
    yrs = sorted({k[:4] for k in days})
    print("갱신", len(days), "일", yrs[0], "~", yrs[-1])


if __name__ == "__main__":
    main()
