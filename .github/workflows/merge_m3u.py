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

# --- Time setup (IST) ---
ist = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(ist)
timestamp = now.strftime("%Y-%m-%d %H:%M IST")
next_update = (now + datetime.timedelta(minutes=config["settings"]["update_interval"])).strftime("%Y-%m-%d %H:%M IST")
hour = now.hour

# --- Greeting logic ---
if 6 <= hour < 12:
    greet = ("☀️ Good Morning, RJM Viewers!", "☀️ Start your Day with RJM Tv 📺")
elif 12 <= hour < 16:
    greet = ("🌤️ Good Afternoon, RJM Viewers!", "🌤️ Enjoy your Afternoon with RJM Tv 📺")
elif 16 <= hour < 18:
    greet = ("🌇 Good Evening, RJM Viewers!", "🌇 Relax this Evening with RJM Tv 📺")
else:
    greet = ("🌙 Good Night, RJM Viewers!", "🌙 Late Night with RJM Tv 📺")

# --- Header/Footer ---
header = f"""#EXTM3U billed-msg="RJM Tv - RJMBTS Network"
# =========================================================
# {greet[0]}
# 🎬 Pushed & Updated by Kittujk
# 💻 Coded & Scripted by @RJMBTS
# 🕒 Last updated on : {timestamp}
# 🔁 Next update    : {next_update}
# =========================================================
"""

footer = f"""
# =========================================================
# {greet[1]}
# ⚡ Powered by RJMBTS ⚡
# =========================================================
"""

# --- Build Master.m3u ---
out_path = config["settings"]["output_file"]
with open(out_path, "w", encoding="utf-8") as master:
    master.write(header)

    for src in sources:
        name = os.path.splitext(os.path.basename(src))[0].upper()
        master.write(f"\n# ======== 📺 {name} SECTION START ========\n")
        try:
            if src.startswith("http"):
                resp = requests.get(src, timeout=20)
                resp.raise_for_status()
                content = resp.text
            else:
                with open(src, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

            # Remove duplicate #EXTM3U lines (keep only top header)
            cleaned = "\n".join(
                [line for line in content.splitlines() if not line.strip().upper().startswith("#EXTM3U")]
            )

            master.write(cleaned.strip() + "\n")
        except Exception as e:
            master.write(f"# ⚠️ Failed to fetch source {src}: {e}\n")
        master.write(f"# ======== 📺 {name} SECTION END ========\n")

    master.write(footer)

print(f"✅ Master.m3u successfully generated at {timestamp} with {len(sources)} sources merged in order.")
