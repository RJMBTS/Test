import yaml, datetime, os, pytz, re

# Load configuration
with open("m3u_merge_config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Load creds.txt sources
sources = []
with open(config["settings"]["source_list"], "r", encoding="utf-8") as f:
    for line in f:
        src = line.strip()
        if src and os.path.exists(src):
            sources.append(src)

if not sources:
    print("❌ No valid sources found in creds.txt.")
    exit(1)

# Collect channels and remove duplicates
seen = set()
channels = []
source_counts = {}

for src in sources:
    name = os.path.splitext(os.path.basename(src))[0]  # e.g., z5.m3u → z5
    count_before = len(channels)

    with open(src, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            url = lines[i + 1].strip() if i + 1 < len(lines) else ""
            key = (lines[i].strip(), url)
            if key not in seen:
                seen.add(key)
                channels.append((lines[i].strip(), url))

    # count channels added from this source
    source_counts[name.upper()] = len(channels) - count_before

# Time setup (IST)
ist = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(ist)
timestamp = now.strftime("%Y-%m-%d %H:%M IST")
next_update = (now + datetime.timedelta(minutes=config["settings"]["update_interval"])).strftime("%Y-%m-%d %H:%M IST")
hour = now.hour

# Determine greeting + matching footer
if 6 <= hour < 12:
    greet = ("☀️ Good Morning, RJM Viewers!", "☀️ Start your Day with RJM Tv 📺")
elif 12 <= hour < 16:
    greet = ("🌤️ Good Afternoon, RJM Viewers!", "🌤️ Enjoy your Afternoon with RJM Tv 📺")
elif 16 <= hour < 18:
    greet = ("🌇 Good Evening, RJM Viewers!", "🌇 Relax this Evening with RJM Tv 📺")
else:
    greet = ("🌙 Good Night, RJM Viewers!", "🌙 Late Night with RJM Tv 📺")

# Build per-source summary line
summary_parts = [f"📺 {name} ➜ {count}" for name, count in source_counts.items()]
source_summary = " | ".join(summary_parts)

# Stats
total = len(channels)
updated = total  # Treat all as updated for now

# Build header
header = f"""#EXTM3U billed-msg="RJM Tv - RJMBTS Network"
# =========================================================
# {greet[0]}
# 🎬 Pushed & Updated by Kittujk
# 💻 Coded & Scripted by @RJMBTS
# 🕒 Last updated on : {timestamp}
# 🔁 Next update     : {next_update}
# 📊 Channels : Total - {total} | Updated - {updated}
# ---------------------------------------------------------
# {source_summary}
# =========================================================
"""

# Footer
footer = f"""
# =========================================================
# {greet[1]}
# ⚡ Powered by RJMBTS ⚡
# =========================================================
"""

# Write Master.m3u
out_path = config["settings"]["output_file"]
with open(out_path, "w", encoding="utf-8") as f:
    f.write(header)
    for extinf, url in channels:
        f.write(f"{extinf}\n{url}\n")
    f.write(footer)

print(f"✅ Master.m3u generated successfully with {total} channels at {timestamp}")
for src, count in source_counts.items():
    print(f"   📺 {src}: {count} channels")
