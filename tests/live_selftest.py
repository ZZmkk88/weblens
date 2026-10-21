"""Live self-test for weblens: boots a real uvicorn server on a scratch
database and walks the whole user flow over HTTP.

Run: .venv/bin/python tests/live_selftest.py
"""
import os
import subprocess
import sys
import tempfile
import time

import httpx

BASE = "http://127.0.0.1:8142"
http = httpx.Client(trust_env=False)

CHROME_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" | {extra}" if extra else ""))
    if not cond:
        raise SystemExit(f"selftest failed at: {name}")


def collect(site_id, path, referrer, ip, ua):
    return http.post(
        BASE + "/api/collect",
        json={
            "site_id": site_id,
            "url": f"https://demo.example.com{path}",
            "referrer": referrer,
        },
        headers={"User-Agent": ua, "X-Forwarded-For": ip},
    )


def main():
    tmp = tempfile.mkdtemp(prefix="weblens-live-")
    env = dict(os.environ)
    env["WEBLENS_DB_PATH"] = os.path.join(tmp, "live.db")
    env["WEBLENS_PORT"] = "8142"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                if http.get(BASE + "/", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.2)
        else:
            raise SystemExit("server did not come up")

        page = http.get(BASE + "/")
        check("首页能打开且是 weblens 页面", page.status_code == 200 and "weblens" in page.text)

        tracker = http.get(BASE + "/tracker.js")
        check(
            "埋点脚本可取回且指向 collect 接口",
            tracker.status_code == 200 and "/api/collect" in tracker.text,
        )

        r = http.post(
            BASE + "/api/login", json={"username": "admin", "password": "admin123"}
        )
        check("登录成功", r.status_code == 200, r.text[:120])
        data = r.json()
        check("首次登录提示改密", data["must_change_password"] is True)
        h = {"Authorization": f"Bearer {data['token']}"}

        r = http.post(
            BASE + "/api/sites",
            json={"name": "演示站", "domain": "https://www.demo.example.com/home"},
            headers=h,
        )
        check("建站成功并规范化域名", r.status_code == 200 and r.json()["domain"] == "demo.example.com", r.text[:160])
        site = r.json()
        check(
            "埋点片段含专属 site_id",
            f'data-weblens-id="{site["site_id"]}"' in site["snippet"],
            site["snippet"],
        )

        ok = True
        for path in ("/pricing", "/pricing", "/docs"):
            rr = collect(
                site["site_id"],
                path,
                "https://www.google.com/search",
                "198.51.100.23",
                CHROME_WIN,
            )
            ok = ok and rr.status_code == 201
        check("访客 A 三次上报全部成功", ok)

        rr = collect(
            site["site_id"],
            "/pricing",
            "https://www.bing.com/search",
            "198.51.100.24",
            SAFARI_IPHONE,
        )
        check("访客 B 上报成功", rr.status_code == 201, rr.text[:120])

        r = http.get(
            BASE + f"/api/sites/{site['id']}/stats",
            params={"range": "today"},
            headers=h,
        )
        stats = r.json()
        check("今日 PV/UV 正确：PV 4、UV 2", r.status_code == 200 and stats["totals"] == {"pv": 4, "uv": 2}, str(stats.get("totals")))
        check(
            "热门页面正确：/pricing 3 次居首",
            stats["top_pages"][0] == {"path": "/pricing", "count": 3},
            str(stats["top_pages"]),
        )
        check(
            "来源排行正确：google.com 3 次居首",
            stats["top_referrers"][0] == {"domain": "google.com", "count": 3},
            str(stats["top_referrers"]),
        )

        r = http.get(
            BASE + f"/api/sites/{site['id']}/stats",
            params={"range": "7d"},
            headers=h,
        )
        week = r.json()
        check(
            "近 7 天趋势长度与合计正确",
            len(week["trend"]) == 7 and sum(d["pv"] for d in week["trend"]) == 4,
            str(week["trend"]),
        )

        r = http.put(
            BASE + f"/api/sites/{site['id']}",
            json={"name": "演示站（改名）"},
            headers=h,
        )
        check("站点改名生效", r.status_code == 200 and r.json()["name"] == "演示站（改名）")

        r = http.delete(BASE + f"/api/sites/{site['id']}", headers=h)
        check("删除站点成功", r.status_code == 200)
        r = http.get(
            BASE + f"/api/sites/{site['id']}/stats",
            params={"range": "today"},
            headers=h,
        )
        check("删除后统计接口返回 404", r.status_code == 404)

        print("LIVE SELFTEST: ALL PASS (15 checks)")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
