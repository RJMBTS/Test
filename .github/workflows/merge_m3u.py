import yaml, datetime, os, pytz, requests

# --- Load configuration ---
config_path = os.path.join(os.path.dirname(__file__), "m3u_merge_config.yml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# --- Load sources from creds.txt (local + remote) ---
sources = []
with open(config["settings"]["source_list"], "r", encoding="utf-8") as f:
    for line in f:
        src = line.strip()
        if not src:
            continue
        if src.startswith(("http://", "https://")) or os.path.exists(src):
            sources.append(src)
        else:
            print(f"⚠️ Skipping invalid source: {src}")

if not sources:
    print("❌ No valid sources found in creds.txt.")
    exit(1)

# --- Collect channels & remove duplicates ---
seen, channels, source_counts = set(), [], {}

for src in sources:
    name = os.path.splitext(os.path.basename(src))[0].upper()
    print(f"🔹 Processing: {name}")
    try:
        if src.startswith("http"):
            resp = requests.get(src, timeout=20)
            resp.raise_for_status()
            lines = resp.text.splitlines()
        else:
            with open(src, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
    except Exception as e:
        print(f"⚠️ Failed to load {src}: {e}")
        continue

    before = len(channels)
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            url = lines[i + 1].strip() if i + 1 < len(lines) else ""
            key = (lines[i].strip(), url)
            if key not in seen:
                seen.add(key)
                channels.append((lines[i].strip(), url))
    source_counts[name] = len(channels) - before

# --- Time setup (IST) ---
ist = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(ist)
timestamp = now.strftime("%Y-%m-%d %H:%M IST")
next_update = (now + datetime.timedelta(minutes=config["settings"]["update_interval"])).strftime("%Y-%m-%d %H:%M IST")
hour = now.hour

# --- Greeting + theme ---
if 6 <= hour < 12:
    greet = ("☀️ Good Morning, RJM Viewers!", "☀️ Start your Day with RJM Tv 📺")
    theme = "#ffef96"
elif 12 <= hour < 16:
    greet = ("🌤️ Good Afternoon, RJM Viewers!", "🌤️ Enjoy your Afternoon with RJM Tv 📺")
    theme = "#fff1b0"
elif 16 <= hour < 18:
    greet = ("🌇 Good Evening, RJM Viewers!", "🌇 Relax this Evening with RJM Tv 📺")
    theme = "#ffd6a5"
else:
    greet = ("🌙 Good Night, RJM Viewers!", "🌙 Late Night with RJM Tv 📺")
    theme = "#d8c9ff"

# --- Build per-source summary ---
summary_parts = [f"📺 {n} ➜ {c}" for n, c in source_counts.items()]
source_summary = " | ".join(summary_parts)
total = len(channels)
updated = total

# --- Header / Footer ---
header = f"""#EXTM3U billed-msg="RJM Tv - RJMBTS Network"
# =========================================================
# {greet[0]}
# 🎬 Pushed & Updated by Kittujk
# 💻 Coded & Scripted by @RJMBTS
# 🕒 Last updated on : {timestamp}
# 🔁 Next update : {next_update}
# 📊 Channels : Total - {total} | Updated - {updated}
# ---------------------------------------------------------
# {source_summary}
# =========================================================
"""
footer = f"""
# =========================================================
# {greet[1]}
# ⚡ Powered by RJMBTS ⚡
# =========================================================
"""

# --- Write Master.m3u with REAL playable links ---
out_path = config["settings"]["output_file"]
with open(out_path, "w", encoding="utf-8") as f:
    f.write(header)
    for extinf, url in channels:
        f.write(f"{extinf}\n{url}\n")
    f.write(footer)

print(f"✅ Master.m3u generated ({total} channels) at {timestamp}")

# --- Build index.html with countdown timer ---
index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RJM Tv – Master.m3u</title>
<style>
  body {{
    font-family:'Segoe UI',Arial,sans-serif;
    background:{theme};
    color:#222;
    text-align:center;
    padding:2rem;
  }}
  h1{{font-size:2rem;margin-bottom:.5rem}}
  .stats{{margin-top:1rem;font-size:1.1rem}}
  .sources{{margin-top:1rem;background:rgba(255,255,255,.7);
           padding:.5rem 1rem;border-radius:8px;display:inline-block}}
  .footer{{margin-top:2rem;font-size:.9rem;color:#555}}
  a.download{{display:inline-block;margin-top:1.5rem;background:#222;color:#fff;
             padding:.6rem 1.2rem;border-radius:6px;text-decoration:none}}
  #timer,#clock{{font-weight:bold}}
</style>
<script>
let seconds=60;
function countdown(){{
  document.getElementById('timer').textContent='⏱ Refreshing in '+seconds+' s';
  seconds--;
  if(seconds<0)location.reload();
}}
function updateClock(){{
  const now=new Date();
  document.getElementById('clock').textContent='🕒 Current Time: '+now.toLocaleTimeString('en-IN',{{
    hour12:false,timeZone:'Asia/Kolkata'
  }})+' IST';
}}
setInterval(countdown,1000);
setInterval(updateClock,1000);
window.onload=function(){{countdown();updateClock();}};
</script>
</head>
<body>
  <h1>{greet[0]}</h1>
  <div class="stats">
    <p>🕒 Last updated on <b>{timestamp}</b></p>
    <p>🔁 Next update <b>{next_update}</b></p>
    <p id="clock"></p>
    <p>📊 Total channels <b>{total}</b></p>
  </div>
  <div class="sources">{source_summary}</div>
  <br>
  <a class="download" href="Master.m3u">📥 Download Master.m3u</a>
  <div id="timer" style="margin-top:1rem;"></div>
  <div class="footer">
    <p>{greet[1]}</p>
    <p>⚡ Powered by <b>RJMBTS</b> ⚡</p>
  </div>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print("🌐 index.html dashboard generated successfully (countdown + live clock).")
