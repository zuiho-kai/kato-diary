#!/usr/bin/env python3
"""把 diary_plugin 生成的日记 JSON 转成 Hugo 文章，有变化就提交推送。

用法：sync_diaries.py <日记目录> <站点仓库目录>
同一天多篇只取最后一篇；内容为空的跳过。
"""
import json
import subprocess
import sys
from pathlib import Path

WEEKDAY = "一二三四五六日"


def main() -> int:
    src, repo = Path(sys.argv[1]), Path(sys.argv[2])
    posts = repo / "content" / "posts"
    posts.mkdir(parents=True, exist_ok=True)
    latest: dict[str, tuple[str, dict]] = {}
    for f in sorted(src.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        content = (d.get("diary_content") or "").strip()
        date = d.get("date")
        if not content or not date:
            continue
        latest[date] = (f.stem, d)
    changed = 0
    for date, (stem, d) in latest.items():
        from datetime import date as _d
        y, m, dd = map(int, date.split("-"))
        wd = WEEKDAY[_d(y, m, dd).weekday()]
        weather = d.get("weather") or ""
        title = f"{m}月{dd}日 星期{wd}" + (f" {weather}" if weather else "")
        hhmmss = stem.split("_")[-1] if "_" in stem else "233000"
        stamp = f"{date}T{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:6]}+08:00"
        body = d["diary_content"].strip()
        text = f'---\ntitle: "{title}"\ndate: {stamp}\n---\n\n{body}\n'
        out = posts / f"{date}.md"
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            out.write_text(text, encoding="utf-8")
            changed += 1
    if not changed:
        print("no change")
        return 0
    run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True)
    run("add", "content/posts")
    run("commit", "-q", "-m", f"日记更新 {max(latest)}")
    run("push", "-q", "origin", "main")
    print(f"pushed {changed} post(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
