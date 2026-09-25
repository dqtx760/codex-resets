# -*- coding: utf-8 -*-
import re, json, html, datetime
from datetime import date, timedelta

ROOT = r"C:\Users\Administrator\WorkBuddy\2026-09-23-13-54-31"
src = open(ROOT + r"\codex_zh.html", encoding="utf-8").read()

# ---------- parse reset calendar cells ----------
resets = {}  # date -> dict(level,type,href,snippet)
for attrs in re.findall(r'class="cg-cell[^"]*"([^>]*)>', src):
    dm = re.search(r'data-date="([^"]+)"', attrs)
    if not dm:
        continue
    d = dm.group(1)
    lvl = re.search(r'data-level="([^"]+)"', attrs)
    rt = re.search(r'data-reset-type="([^"]+)"', attrs)
    href = re.search(r'href="([^"]+)"', attrs)
    snip = re.search(r'data-snippet="([^"]*)"', attrs)
    resets[d] = {
        "level": lvl.group(1) if lvl else "0",
        "type": rt.group(1) if rt else "regular",
        "href": href.group(1) if href else "",
        "snippet": snip.group(1) if snip else "",
    }

# ---------- parse log items (54) ----------
logs = []
for block in re.findall(r'<li class="log-item"[^>]*data-tweet-id="([^"]+)"[^>]*>(.*?)</li>', src, re.S):
    tid, b = block
    dtm = re.search(r'data-role="relative-time" data-datetime="([^"]+)"', b)
    txt = re.search(r'<p class="log-item-text"[^>]*>(.*?)</p>', b, re.S)
    link = re.search(r'<a class="log-item-link" href="([^"]+)"', b)
    if not (dtm and txt):
        continue
    text = html.unescape(txt.group(1))
    text = re.sub(r'\s*\n\s*\n\s*', '\n\n', text).strip()
    logs.append({
        "tid": tid,
        "datetime": dtm.group(1),
        "text": text,
        "link": link.group(1) if link else "",
    })

print("resets:", len(resets), "logs:", len(logs))

# ---------- calendar grid ----------
start = date(2025, 9, 14)  # Sunday
today = date(2026, 9, 23)
WEEKS = 54
cells_html = []
for w in range(WEEKS):
    for d in range(7):
        day = start + timedelta(weeks=w, days=d)
        col = w + 1
        row = d + 2
        ds = day.isoformat()
        if day > today:
            cells_html.append(f'<span class="cg-cell cg-cell--future" style="grid-column:{col};grid-row:{row}" aria-hidden="true"></span>')
        elif ds in resets and resets[ds]["level"] == "1":
            r = resets[ds]
            title = (r["snippet"][:120] + "…") if len(r["snippet"]) > 120 else r["snippet"]
            title = html.escape(title).replace('"', "&quot;")
            cells_html.append(
                f'<a class="cg-cell" data-level="1" data-reset-type="{r["type"]}" '
                f'data-date="{ds}" style="grid-column:{col};grid-row:{row}" '
                f'title="{title}" href="{r["href"]}" target="_blank" rel="noopener noreferrer"></a>')
        else:
            cells_html.append(f'<button type="button" class="cg-cell" data-level="0" data-date="{ds}" style="grid-column:{col};grid-row:{row}" aria-label="{ds}：未重置"></button>')

# month labels (merge consecutive same-month weeks)
months_html = []
prev_month = None
run_start = None
def flush(run_start, run_end, month):
    if run_start is not None:
        months_html.append(f'<span class="cg-month" style="grid-column:{run_start} / span {run_end-run_start+1};grid-row:1">{month}月</span>')
for w in range(WEEKS):
    fd = start + timedelta(weeks=w)
    m = fd.month
    if m != prev_month:
        if prev_month is not None:
            flush(run_start, w - 1, prev_month)
        run_start = w + 1
        prev_month = m
flush(run_start, WEEKS - 1, prev_month)

# ---------- log html ----------
def esc(t):
    return html.escape(t)

def fmt_abs(iso):
    try:
        dtobj = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return "%d年%d月%d日 %02d:%02d UTC" % (dtobj.year, dtobj.month, dtobj.day, dtobj.hour, dtobj.minute)
    except Exception:
        return iso

def log_item_li(it):
    dt = it["datetime"]
    abs_txt = fmt_abs(dt)
    return f'''    <li class="log-item" data-tweet-id="{esc(it['tid'])}">
      <img class="log-avatar" src="avatar.jpg" alt="" aria-hidden="true" width="44" height="44" />
      <div class="log-bubble">
        <div class="log-item-meta">
          <span class="log-item-time" data-role="relative-time" data-datetime="{esc(dt)}"></span>
          <span class="log-item-abs" data-role="absolute-time" data-datetime="{esc(dt)}">{esc(abs_txt)}</span>
        </div>
        <p class="log-item-text" data-role="tweet-display-text">{esc(it['text'])}</p>
        <a class="log-item-link" href="{esc(it['link'])}" target="_blank" rel="noopener noreferrer">在 X 查看 &rarr;</a>
      </div>
    </li>'''

first3 = "\n".join(log_item_li(it) for it in logs[:3])
rest = "\n".join(log_item_li(it) for it in logs[3:])

# ---------- sponsors (APIMart kept + custom links) ----------
sponsors = [
    ("APIMart.AI", "官方图像与视频 API — 80% 优惠。GPT-Image-2 每张低至 $0.006。", "img", "https://codex-resets.com/apimart.png", "https://apimart.ai/"),
    ("codex指南", "Codex 使用指南与实战技巧合集。", "emoji", "📘", "https://gpt.dqtx.cc/"),
    ("GPT 代充", "GPT 会员低价代充值，稳定到账。", "emoji", "💳", "https://ai.dqtx.cc/"),
    ("魔法工具", "稳定好用的魔法上网工具推荐。", "emoji", "✨", "https://77.dqtx.cc/"),
]
sponsor_html = ""
for name, desc, kind, val, href in sponsors:
    if kind == "img":
        logo = f'<span class="sponsor-logo sponsor-logo--image"><img src="{val}" alt="" width="36" height="36" loading="lazy" referrerpolicy="no-referrer" /></span>'
    else:
        logo = f'<span class="sponsor-logo sponsor-emoji">{val}</span>'
    sponsor_html += f'''<a class="sponsor-card sponsor-card--compact" href="{href}" target="_blank" rel="noopener noreferrer">
  <span class="sponsor-label">推荐</span>
  {logo}
  <span class="sponsor-copy"><strong>{esc(name)}</strong><span>{esc(desc)}</span></span>
</a>'''

latest = logs[0]
latest_dt = latest["datetime"]

CAL = "\n          ".join(cells_html)
MON = "\n          ".join(months_html)

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="theme-color" content="#fff4dd" />
<title>Codex 额度重置追踪与历史记录 | Codex Resets</title>
<meta name="description" content="追踪最新的 OpenAI Codex 额度重置，查看重置历史，并在新重置公布时收到通知。" />
<link rel="icon" href="avatar.jpg" type="image/jpeg" />
<style>
@font-face{font-family:"Baloo 2";font-style:normal;font-weight:700;font-display:optional;src:url(https://codex-resets.com/fonts/Baloo2-Bold.woff2) format("woff2")}
@font-face{font-family:"Baloo 2";font-style:normal;font-weight:800;font-display:optional;src:url(https://codex-resets.com/fonts/Baloo2-ExtraBold.woff2) format("woff2")}
@font-face{font-family:"GenSen Rounded";font-style:normal;font-weight:700;font-display:swap;src:url(https://codex-resets.com/fonts/GenSenRounded-Bold-UI.woff2) format("woff2")}
@font-face{font-family:"GenSen Rounded";font-style:normal;font-weight:800;font-display:swap;src:url(https://codex-resets.com/fonts/GenSenRounded-Heavy-UI.woff2) format("woff2")}
:root{--paper:#fff4dd;--ink:#26201a;--ink-2:#5c5347;--ink-3:#877b6b;--accent:#ff5c2b;--sun:#ffd84d;--watch-paper:#fff0bd;--rose:#ffb9cc;--sky:#a5dcff;--peach:#ffb07a;--card:#fffdf7;--cg-empty:#f1e3c4;--cg-fill:var(--accent);--cg-banked:var(--peach);--accent-hover:#ee4518;--sun-hover:#ffe070;--on-accent:var(--card);--on-sun:var(--ink);--on-rose:var(--ink);--on-sky:var(--ink);--banked-copy:#8b3d1f;--watch-copy:#675015;--dot-ink:#26201a1a;--shadow-ink:var(--ink);--border:2px solid var(--ink);--shadow:4px 4px 0 var(--shadow-ink);--shadow-sm:3px 3px 0 var(--shadow-ink);--radius:14px;--font-display:"Baloo 2","Arial Rounded MT Bold",system-ui,sans-serif;--font-body:system-ui,-apple-system,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;--font-mono:ui-monospace,"SF Mono","Cascadia Code",Menlo,Consolas,monospace;--cell-size:22px}
[data-theme=dark]{--paper:oklch(18% .012 70);--ink:oklch(93% .025 80);--ink-2:oklch(76% .025 75);--ink-3:oklch(66% .024 72);--accent:oklch(67% .2 38);--sun:oklch(75% .135 82);--watch-paper:oklch(30% .055 72);--rose:oklch(70% .12 355);--sky:oklch(71% .095 232);--peach:oklch(78% .12 48);--card:oklch(24% .014 70);--cg-empty:oklch(35% .022 75);--cg-banked:var(--peach);--accent-hover:oklch(62% .2 38);--sun-hover:oklch(79% .14 82);--on-accent:oklch(20% .03 38);--on-sun:oklch(22% .04 82);--on-rose:oklch(20% .03 350);--on-sky:oklch(20% .03 235);--banked-copy:var(--peach);--watch-copy:oklch(86% .09 82);--dot-ink:#f6e8cf14;--shadow-ink:oklch(8% .005 70);--shadow-soft:#0302028c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font-body);line-height:1.5;-webkit-font-smoothing:antialiased}
.page{max-width:760px;margin:0 auto;padding:0 20px 80px}
.masthead{display:flex;align-items:center;gap:16px;padding:34px 0 4px;position:relative}
.masthead-brand{display:flex;align-items:center;gap:14px;min-width:0}
.masthead-avatar{border:var(--border);width:44px;height:44px;box-shadow:var(--shadow-sm);border-radius:50%;transform:rotate(-4deg);flex:none}
.masthead-title{font-family:var(--font-display);letter-spacing:-.01em;margin:0;font-size:clamp(26px,4.5vw,34px);font-weight:800;line-height:1.05}
.masthead-side{margin-left:auto;display:flex;align-items:center;gap:4px;white-space:nowrap}
.lang-wrap{position:relative}
.language-toggle,.x-link,.theme-toggle{width:40px;height:40px;color:var(--ink);cursor:pointer;background:0 0;border:0;border-radius:50%;flex:0 0 40px;place-items:center;padding:0;display:inline-grid;position:relative;transition:transform .1s}
.language-toggle:before,.x-link:before,.theme-toggle:before{content:"";box-sizing:border-box;border:var(--border);background:var(--card);box-shadow:1px 1px 0 var(--shadow-ink);border-radius:50%;position:absolute;inset:5px;pointer-events:none}
.language-toggle:active,.x-link:active,.theme-toggle:active{transform:translate(2px,2px)}
.language-toggle:active:before,.x-link:active:before,.theme-toggle:active:before{box-shadow:0 0 0 var(--shadow-ink)}
.language-toggle:hover,.x-link:hover,.theme-toggle:hover{transform:translate(-1px,-1px)}
.language-toggle:hover:before,.x-link:hover:before,.theme-toggle:hover:before{box-shadow:2px 2px 0 var(--shadow-ink)}
.language-toggle svg,.x-link svg,.theme-toggle svg{width:20px;height:20px;z-index:1;fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round}
.language-menu{position:absolute;top:46px;right:0;background:var(--card);border:var(--border);box-shadow:var(--shadow-sm);border-radius:12px;padding:6px;display:flex;flex-direction:column;min-width:130px;z-index:20}
.language-menu[popover]:not(:popover-open){display:none}
.language-menu a{font-family:var(--font-body);color:var(--ink);text-decoration:none;padding:8px 12px;border-radius:8px;font-size:14px}
.language-menu a:hover{background:var(--sun)}
.language-menu a[aria-current=page]{font-weight:800;background:var(--sun)}
.theme-toggle-icon{fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round;width:18px;height:18px;position:absolute;inset:0;transition:opacity .12s,transform .12s}
.theme-toggle-icons{position:relative;width:18px;height:18px;z-index:1;display:block}
.theme-toggle-icon--moon{opacity:1;transform:scale(1)}
.theme-toggle-icon--sun{opacity:0;transform:scale(.75)}
[data-theme=dark] .theme-toggle-icon--moon{opacity:0;transform:scale(.75)}
[data-theme=dark] .theme-toggle-icon--sun{opacity:1;transform:scale(1)}
.hero-explainer{font-size:18px;line-height:1.6;margin:18px 0 18px}
.hero-explainer a{color:var(--accent);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.hero-toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:18px}
.subscription-actions{display:flex;flex-wrap:wrap;gap:9px;align-items:center}
.subscription-action{border:var(--border);min-height:40px;color:var(--ink);box-shadow:var(--shadow-sm);font-family:var(--font-display);cursor:pointer;border-radius:999px;align-items:center;gap:7px;padding:8px 14px;font-size:14px;font-weight:700;line-height:1.2;display:inline-flex;text-decoration:none;background:var(--card)}
.subscription-action:active{box-shadow:0 0 0 var(--shadow-ink);transform:translate(3px,3px)}
.telegram-link:hover{background:var(--sky);color:var(--on-sky)}
.email-toggle:hover{background:var(--rose);color:var(--on-rose)}
.subscription-action svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round}
.push-toggle{background:var(--accent);color:var(--on-accent)}
.push-toggle:hover{background:var(--accent-hover)}
.push-toggle svg{fill:currentColor}
.push-toggle .push-count-dot{width:7px;height:7px;border-radius:50%;background:var(--sun);display:inline-block}
.time-setting{margin-left:auto;display:flex;flex:none}
.time-toggle{border:var(--border);background:var(--card);color:var(--ink);font-family:var(--font-display);font-weight:700;font-size:13px;padding:9px 14px;cursor:pointer;line-height:1.2;box-shadow:var(--shadow-sm)}
.time-toggle:first-child{border-radius:999px 0 0 999px}
.time-toggle:last-child{border-radius:0 999px 999px 0;border-left-width:0}
.time-toggle.is-active{background:var(--sun);color:var(--on-sun)}
.time-toggle:not(.is-active):hover{background:var(--rose);color:var(--on-rose)}
.scheduled-card{background:var(--watch-paper);border:var(--border);border-radius:var(--radius);box-shadow:var(--shadow-sm);padding:14px 18px;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.scheduled-card .sc-label{font-family:var(--font-mono);letter-spacing:.1em;text-transform:uppercase;font-size:11px;color:var(--watch-copy);font-weight:700}
.scheduled-card .sc-main{font-family:var(--font-display);font-weight:800;font-size:20px;margin-top:2px}
.scheduled-card a{color:var(--accent);font-weight:800;text-decoration:none;font-family:var(--font-display)}
.hero-card{background:var(--card);background-image:radial-gradient(var(--dot-ink) 1.5px,transparent 1.5px);border:var(--border);border-radius:var(--radius);box-shadow:6px 6px 0 var(--shadow-ink);background-size:18px 18px;padding:24px 26px 28px;transform:rotate(-.4deg);display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"label label" "figure plea" "footer footer";gap:14px 32px}
.hero-label{grid-area:label;font-family:var(--font-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2);margin:0;font-size:12px;display:block}
.hero-figure{grid-area:figure;justify-self:start;font-family:var(--font-display);letter-spacing:-.02em;color:var(--on-sun);background:var(--sun);border-radius:10px;padding:0 14px 4px;font-size:clamp(40px,7.5vw,64px);font-weight:800;line-height:1.1;display:inline-block;transform:rotate(-1.2deg)}
.hero-footer{grid-area:footer;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px}
.hero-sub{margin:0;font-size:14px;color:var(--ink-2);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.hero-sub strong{color:var(--banked-copy);font-family:var(--font-display)}
.reset-plea{display:flex;align-items:center}
.reset-plea-action{position:relative;display:inline-flex}
.reset-plea-bursts{position:absolute;left:50%;top:-4px;pointer-events:none;z-index:5}
.reset-plea-burst{position:absolute;bottom:0;pointer-events:none;animation:reset-plea-burst .9s ease-out forwards}
@keyframes reset-plea-burst{0%{opacity:1;transform:translate(0,0) scale(.6)}100%{opacity:0;transform:translate(var(--dx,0),-56px) scale(1.15)}}
@keyframes reset-plea-hands{0%{transform:rotate(0) scale(1)}40%{transform:rotate(-14deg) scale(1.3)}100%{transform:rotate(0) scale(1)}}
.reset-plea-button.is-pleading .reset-plea-button-emoji{animation:.26s cubic-bezier(.34,1.56,.64,1) reset-plea-hands}
.reset-plea-button{border:var(--border);background:var(--sun);min-height:34px;box-shadow:2px 2px 0 var(--shadow-ink);color:var(--on-sun);font-family:var(--font-display);cursor:pointer;touch-action:manipulation;user-select:none;border-radius:10px;justify-content:center;align-items:center;gap:5px;padding:6px 12px;font-size:13px;font-weight:800;line-height:1;display:inline-flex;transition:transform 80ms,box-shadow 80ms,background .15s}
.reset-plea-button:hover{background:var(--sun-hover)}
.reset-plea-button:active{box-shadow:1px 1px 0 var(--shadow-ink);transform:translate(2px,2px)}
.reset-plea-button-emoji{font-size:16px;display:inline-block}
.reset-plea-count{font-variant-numeric:tabular-nums}
.stat-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:30px 0}
.stat-tile{border:var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:14px 18px 16px;transition:transform .2s cubic-bezier(.34,1.56,.64,1)}
.stat-tile--sun{background:var(--sun);color:var(--on-sun);transform:rotate(-1deg)}
.stat-tile--rose{background:var(--rose);color:var(--on-rose);transform:rotate(.8deg)}
.stat-tile--sky{background:var(--sky);color:var(--on-sky);transform:rotate(-.6deg)}
.stat-tile:hover{transform:rotate(0) translateY(-3px)}
.stat-tile dt{font-family:var(--font-mono);letter-spacing:.04em;text-transform:uppercase;color:currentColor;opacity:.75;margin:0 0 4px;font-size:11px}
.stat-tile dd{font-family:var(--font-display);color:currentColor;white-space:nowrap;margin:0;font-size:30px;font-weight:700;line-height:1.1}
.sponsor-mobile{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:8px 0 30px}
.sponsor-card{border:var(--border);border-radius:var(--radius);background:var(--card);color:var(--ink);box-shadow:var(--shadow-sm);text-align:left;gap:10px;padding:12px;display:flex;align-items:center;text-decoration:none;transition:transform .14s,box-shadow .14s;position:relative;overflow:hidden}
.sponsor-card:hover{color:var(--ink);box-shadow:5px 5px 0 var(--shadow-ink);transform:translate(-1px,-1px)}
.sponsor-label{position:absolute;top:6px;right:10px;font-family:var(--font-mono);font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3)}
.sponsor-logo{flex:0 0 34px;width:34px;height:34px}
.sponsor-logo img{width:34px;height:34px;border-radius:9px;display:block}
.sponsor-emoji{display:flex;align-items:center;justify-content:center;font-size:18px;background:var(--sun);border:var(--border);border-radius:9px}
.sponsor-copy{display:flex;flex-direction:column;min-width:0}
.sponsor-copy strong{font-family:var(--font-display);font-size:14px}
.sponsor-copy span{font-size:12px;color:var(--ink-2);line-height:1.3;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.sponsor-logo img{width:34px;height:34px;border-radius:9px;display:block}
.sponsor-copy{display:flex;flex-direction:column;min-width:0}
.sponsor-copy strong{font-family:var(--font-display);font-size:14px}
.sponsor-copy span{font-size:12px;color:var(--ink-2);line-height:1.3;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:34px 0 14px}
.section-head h2{font-family:var(--font-display);font-size:24px;margin:0}
.section-sub{color:var(--ink-3);font-size:13px;margin:0;display:flex;gap:14px;flex-wrap:wrap}
.legend-item{display:inline-flex;align-items:center;gap:5px;font-size:12px}
.legend-chip{border:1.5px solid var(--ink);background:var(--cg-empty);vertical-align:-1px;border-radius:3px;width:11px;height:11px;display:inline-block}
.legend-chip--regular{background:var(--cg-fill)}
.legend-chip--banked{background:var(--cg-banked)}
.graph-card{border:var(--border);border-radius:var(--radius);box-shadow:var(--shadow-sm);background:var(--card);padding:16px;overflow:hidden}
.cg-container{display:flex;gap:6px}
.cg-weekdays{display:grid;grid-template-rows:20px repeat(7,var(--cell-size));font-size:10px;color:var(--ink-3);font-family:var(--font-mono)}
.cg-weekday{display:flex;align-items:center}
.cg-scroll{overflow-x:auto;padding-bottom:6px}
.cg-grid{display:grid;grid-template-columns:repeat(54,var(--cell-size));grid-template-rows:20px repeat(7,var(--cell-size));gap:3px}
.cg-month{grid-row:1;font-family:var(--font-mono);font-size:10px;color:var(--ink-3);align-self:end}
.cg-cell{width:var(--cell-size);height:var(--cell-size);background:var(--cg-empty);border:none;border-radius:6px;padding:0;cursor:pointer;transition:transform .15s cubic-bezier(.34,1.56,.64,1)}
.cg-cell[data-level="1"]{background:var(--cg-fill);border:1.5px solid var(--ink);box-shadow:1.5px 1.5px 0 var(--shadow-ink)}
.cg-cell[data-reset-type=banked]{background:var(--cg-banked)}
.cg-cell:hover,.cg-cell:focus-visible{outline:none;transform:scale(1.22)}
.cg-cell[data-level="1"]:hover{transform:scale(1.25) rotate(6deg)}
.cg-cell--future{cursor:default;background:0 0}
.cg-cell--future:hover{transform:none}
.log-section{margin-top:10px}
.log-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:18px}
.log-item{display:flex;align-items:flex-start;gap:12px}
.log-avatar{border:var(--border);width:40px;height:40px;box-shadow:2px 2px 0 var(--shadow-ink);border-radius:50%;flex:none;margin-top:4px}
.log-bubble{background:var(--card);border:var(--border);min-width:0;box-shadow:var(--shadow);border-radius:16px;flex:1;padding:14px 18px;position:relative}
.log-bubble:before{content:"";background:var(--card);border-left:var(--border);border-bottom:var(--border);width:13px;height:13px;position:absolute;top:18px;left:-8px;transform:rotate(45deg)}
.log-item-meta{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;margin-bottom:8px}
.log-item-time{font-family:var(--font-display);background:var(--sun);color:var(--on-sun);border:1.5px solid var(--ink);border-radius:999px;padding:1px 10px 2px;font-size:14px;font-weight:700;white-space:nowrap}
.log-item-abs{font-family:var(--font-mono);color:var(--ink-3);font-size:11px}
.log-item-text{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;color:var(--ink);margin:0;font-size:16px;line-height:1.5}
.log-item-link{font-family:var(--font-mono);margin-top:10px;font-size:12px;display:inline-block;color:var(--accent);font-weight:700;text-decoration:none}
.log-more{text-align:center;margin-top:18px}
.log-more .log-list--more{text-align:left}
.log-more-toggle{cursor:pointer;font-family:var(--font-display);font-weight:800;color:var(--ink);border:var(--border);box-shadow:var(--shadow-sm);background:var(--card);border-radius:999px;padding:10px 18px;display:inline-flex;align-items:center;gap:8px;list-style:none}
.log-more-toggle::-webkit-details-marker{display:none}
.log-more[open] .log-more-label-closed{display:none}
.log-more:not([open]) .log-more-label-open{display:none}
.log-more-arrow{transition:transform .2s}
.log-more[open] .log-more-arrow{transform:rotate(180deg)}
.log-list--more{margin-top:18px}
footer.foot{margin-top:50px;text-align:center;color:var(--ink-3);font-size:13px;font-family:var(--font-mono)}
footer.foot a{color:var(--ink-2)}
.visually-hidden{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (max-width:560px){.stat-row{grid-template-columns:1fr;gap:10px}.hero-card{grid-template-columns:1fr;grid-template-areas:"label" "figure" "plea" "footer"}.sponsor-mobile{grid-template-columns:1fr}}
</style>
<script>
(function(){var s="codex-resets-theme";var r=document.documentElement;function ap(t){r.dataset.theme=t;r.style.colorScheme=t;document.querySelectorAll('meta[name=theme-color]').forEach(function(m){m.setAttribute('content',t==='dark'?'#17130f':'#fff4dd')})}var p=null;try{p=localStorage.getItem(s)}catch(e){}ap(p||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));document.addEventListener('click',function(e){if(e.target.closest&&e.target.closest('[data-role=theme-toggle]')){var n=r.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem(s,n)}catch(e){}ap(n)}});
function rel(d){var diff=Date.now()-new Date(d).getTime();var m=Math.floor(diff/60000);if(m<1)return'刚刚';if(m<60)return m+'分钟前';var h=Math.floor(m/60);if(h<24)return h+'小时前';var d2=Math.floor(h/24);if(d2<30)return d2+'天前';var mo=Math.floor(d2/30);return mo+'个月前'}
function init(){
document.querySelectorAll('[data-role=relative-time]').forEach(function(el){el.textContent=rel(el.dataset.datetime)});
var btn=document.querySelector('[data-role=reset-plea-button]');
if(btn){
  var countEl=btn.querySelector('[data-role=reset-plea-count]');
  var base=163049,key='codex-resets-thanks',extra=0;
  try{extra=parseInt(localStorage.getItem(key)||'0',10)||0}catch(e){}
  function render(){countEl.textContent=(base+extra).toLocaleString('en-US')}
  render();
  btn.addEventListener('click',function(){
    extra++;try{localStorage.setItem(key,String(extra))}catch(e){}
    render();
    btn.classList.remove('is-pleading');void btn.offsetWidth;btn.classList.add('is-pleading');
    var holder=document.querySelector('[data-role=reset-plea-bursts]');
    if(holder){for(var i=0;i<3;i++){(function(){var sp=document.createElement('span');sp.className='reset-plea-burst';sp.textContent='🙏';sp.style.left=((Math.random()*70-10))+'px';sp.style.setProperty('--dx',(Math.random()*28-14)+'px');holder.appendChild(sp);setTimeout(function(){sp.remove()},900)})()}}
  });
  btn.addEventListener('animationend',function(){btn.classList.remove('is-pleading')});
}
}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init)}else{init()}
})();
</script>
</head>
<body>
<div class="page">
  <header class="masthead">
    <div class="masthead-brand">
      <img class="masthead-avatar" src="avatar.jpg" alt="" aria-hidden="true" width="44" height="44" />
      <h1 class="masthead-title">Codex Resets</h1>
    </div>
    <div class="masthead-side">
      <div class="lang-wrap">
        <button class="language-toggle" type="button" popovertarget="language-menu" aria-label="语言" title="语言">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a18 18 0 0 1 0 18 18 18 0 0 1 0-18Z"/></svg>
        </button>
        <nav class="language-menu" id="language-menu" popover="auto" aria-label="语言">
          <a href="https://codex-resets.com/" lang="en" hreflang="en" rel="nofollow">English</a>
          <a href="https://codex-resets.com/zh-CN" lang="zh-CN" hreflang="zh-CN" rel="nofollow" aria-current="page" autofocus>简体中文</a>
          <a href="https://codex-resets.com/zh-TW" lang="zh-TW" hreflang="zh-TW" rel="nofollow">繁體中文</a>
          <a href="https://codex-resets.com/ja" lang="ja" hreflang="ja" rel="nofollow">日本語</a>
          <a href="https://codex-resets.com/ko" lang="ko" hreflang="ko" rel="nofollow">한국어</a>
        </nav>
      </div>
      <a class="x-link" href="https://github.com/dqtx760" target="_blank" rel="noopener noreferrer" title="在 GitHub 关注 dqtx760" aria-label="在 GitHub 关注 dqtx760">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.8 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17 4.7 18 5 18 5c.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.5-2.7 5.5-5.3 5.8.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.6-1.5 7.9-5.8 7.9-10.9C23.5 5.7 18.3.5 12 .5Z"/></svg>
      </a>
      <a class="x-link" href="https://x.com/dqtx760" target="_blank" rel="noopener noreferrer" title="在 X 关注 dqtx760" aria-label="在 X 关注 dqtx760">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.23 10.16 22.1 1h-1.87l-6.84 7.96L8.04 1H1.5l8.26 12.03L1.5 23h1.87l7.22-8.4L15.96 23H22.5l-8.27-12.84Zm-2.56 2.97-.83-1.19L4.04 2.43h2.86l5.34 7.64.84 1.19 6.94 9.93h-2.86l-5.49-7.06Z"/></svg>
      </a>
      <button class="theme-toggle" type="button" data-role="theme-toggle" aria-label="切换明暗主题" title="切换明暗主题">
        <span class="theme-toggle-icons" aria-hidden="true">
          <svg class="theme-toggle-icon theme-toggle-icon--moon" viewBox="0 0 24 24"><path d="M20 15.2A8.5 8.5 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2Z"/></svg>
          <svg class="theme-toggle-icon theme-toggle-icon--sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        </span>
      </button>
    </div>
  </header>

  <main>
    <section class="hero" aria-label="当前状态">
      <p class="hero-explainer">我们帮你关注 <a href="https://x.com/thsottiaux" target="_blank" rel="noopener noreferrer">@thsottiaux</a> 发布的 Codex 重置消息，省得你反复刷推。</p>
      <div class="hero-toolbar">
        <div class="subscription-actions" role="group" aria-label="重置通知">
          <button class="subscription-action push-toggle" type="button" aria-pressed="true" title="Codex 重置时接收浏览器通知">
            <svg class="push-toggle-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>
            <span>浏览器通知已开启</span>
          </button>
          <a class="subscription-action telegram-link" href="https://t.me/+Vk17JyylJkdjMmU1" target="_blank" rel="noopener noreferrer" title="在 Telegram 接收同样的通知">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22 2 9.6 14.4M22 2l-7.9 20-4.5-7.6L2 10l20-8Z"/></svg>
            <span>telegram</span>
          </a>
          <button class="subscription-action email-toggle" type="button" title="Codex 重置确认后接收邮件">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5h18v14H3zM3 6l9 7 9-7"/></svg>
            <span>邮件</span>
          </button>
        </div>
        <div class="time-setting" role="group" aria-label="时间显示">
          <button class="time-toggle is-active" type="button" aria-pressed="true">Tibo 时间</button>
          <button class="time-toggle" type="button" aria-pressed="false">本地时间</button>
        </div>
      </div>

      <div class="scheduled-card">
        <div>
          <div class="sc-label">已安排重置</div>
          <div class="sc-main">约 9 小时内 · 最晚 9月23日周三 14:59</div>
        </div>
        <a href="https://x.com/dqtx760" target="_blank" rel="noopener noreferrer">查看公告 &nearr;</a>
      </div>

      <div class="hero-card">
        <span class="hero-label">最近一次 Codex 重置</span>
        <span class="hero-figure" data-role="relative-time" data-datetime="__LATEST__"></span>
        <div class="reset-plea" data-mode="thanks">
          <div class="reset-plea-action">
            <button class="reset-plea-button" type="button" data-role="reset-plea-button" aria-label="求重置" title="求重置">
              <span class="reset-plea-button-emoji" aria-hidden="true">🙏</span>
              <span class="reset-plea-button-label">求重置</span>
              <span class="reset-plea-count" data-role="reset-plea-count">163,049</span>
            </button>
            <span class="reset-plea-bursts" data-role="reset-plea-bursts" aria-hidden="true"></span>
          </div>
        </div>
        <div class="hero-footer">
          <p class="hero-sub hero-sub--banked">
            <strong>备用重置额度</strong><span aria-hidden="true">·</span>
            <span data-role="absolute-time">9月22日 11:23</span>
          </p>
        </div>
      </div>
    </section>

    <dl class="stat-row">
      <div class="stat-tile stat-tile--sun"><dt>重置次数</dt><dd class="mono">54</dd></div>
      <div class="stat-tile stat-tile--rose"><dt>平均重置间隔</dt><dd class="mono">7.0天</dd></div>
      <div class="stat-tile stat-tile--sky"><dt>最长等待</dt><dd class="mono">67.7天</dd></div>
    </dl>

    <div class="sponsor-mobile" aria-label="推荐工具">__SPONSORS__</div>

    <section class="graph-section" aria-labelledby="graph-heading">
      <div class="section-head">
        <h2 id="graph-heading">Codex 重置历史</h2>
        <p class="section-sub graph-legend">
          <span class="legend-item"><span class="legend-chip legend-chip--regular"></span> 常规</span>
          <span class="legend-item"><span class="legend-chip legend-chip--banked"></span> 备用</span>
          <span class="legend-item"><span class="legend-chip"></span> 未重置</span>
        </p>
      </div>
      <div class="graph-card">
        <div class="cg-container">
          <div class="cg-weekdays" style="grid-template-rows:20px repeat(7,var(--cell-size))"><span class="cg-weekday" style="grid-row:2"></span><span class="cg-weekday" style="grid-row:3">周一</span><span class="cg-weekday" style="grid-row:4"></span><span class="cg-weekday" style="grid-row:5">周三</span><span class="cg-weekday" style="grid-row:6"></span><span class="cg-weekday" style="grid-row:7">周五</span><span class="cg-weekday" style="grid-row:8"></span></div>
          <div class="cg-scroll">
            <div class="cg-grid" style="grid-template-columns:repeat(54,var(--cell-size));grid-template-rows:20px repeat(7,var(--cell-size))">
              __MONTHS__
              __CELLS__
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="log-section" aria-labelledby="log-heading">
      <div class="section-head">
        <h2 id="log-heading">Codex 重置公告</h2>
        <p class="section-sub">每次公告，都留有记录</p>
      </div>
      <ol class="log-list">
__FIRST3__
      </ol>
      <details class="log-more">
        <summary class="log-more-toggle">
          <span class="log-more-label-closed">查看全部 54 次重置</span>
          <span class="log-more-label-open">收起</span>
          <span class="log-more-arrow" aria-hidden="true">&darr;</span>
        </summary>
        <ol class="log-list log-list--more" start="4">
__REST__
        </ol>
      </details>
    </section>

    <footer class="foot">
      <p>本页为 <a href="https://codex-resets.com/zh-CN" target="_blank" rel="noopener noreferrer">codex-resets.com</a> 的静态复刻快照 · 数据截至 2026-09-23</p>
    </footer>
  </main>
</div>
</body>
</html>
"""

# absolute time for latest
latest_abs = fmt_abs(latest_dt)

HTML = (HTML
    .replace("__LATEST__", latest_dt)
    .replace("__LATEST_ABS__", latest_abs)
    .replace("__SPONSORS__", sponsor_html)
    .replace("__MONTHS__", MON)
    .replace("__CELLS__", CAL)
    .replace("__FIRST3__", first3)
    .replace("__REST__", rest))

open(ROOT + r"\index.html", "w", encoding="utf-8").write(HTML)
print("WROTE index.html", len(HTML), "bytes; logs:", len(logs), "cells:", len(cells_html))
