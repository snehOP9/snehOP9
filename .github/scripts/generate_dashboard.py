import collections
import datetime as dt
import html
import json
import os
import urllib.request

OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "snehOP9")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT = os.getenv("DASHBOARD_OUT", "dist/profile-dashboard.svg")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "snehOP9-profile-dashboard",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


user = get_json(f"https://api.github.com/users/{OWNER}")
repos = []
for page in range(1, 4):
    batch = get_json(
        f"https://api.github.com/users/{OWNER}/repos"
        f"?type=owner&sort=updated&per_page=100&page={page}"
    )
    repos.extend(batch)
    if len(batch) < 100:
        break

owned = [r for r in repos if not r.get("fork")]
stars = sum(int(r.get("stargazers_count", 0)) for r in owned)
forks = sum(int(r.get("forks_count", 0)) for r in owned)
followers = int(user.get("followers", 0))
public_repos = int(user.get("public_repos", len(repos)))

languages = collections.Counter(
    r.get("language") for r in owned if r.get("language")
)
top_languages = languages.most_common(5)
max_lang = max((count for _, count in top_languages), default=1)

recent_repo = "—"
if owned:
    latest = max(owned, key=lambda r: r.get("pushed_at") or "")
    recent_repo = latest.get("name") or "—"

refreshed = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y")
esc_owner = html.escape(OWNER)
esc_recent = html.escape(recent_repo)

palette = {
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Python": "#3572A5",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Java": "#B07219",
    "Dart": "#00B4AB",
    "C": "#555555",
    "C++": "#F34B7D",
    "Shell": "#89E051",
}
fallback = ["#22D3EE", "#8B5CF6", "#F59E0B", "#34D399", "#F472B6"]

metric_cards = [
    ("PUBLIC REPOS", str(public_repos)),
    ("STARS EARNED", str(stars)),
    ("FOLLOWERS", str(followers)),
    ("FORKS", str(forks)),
]

card_x = [54, 326, 598, 870]
cards = []
for i, (label, value) in enumerate(metric_cards):
    x = card_x[i]
    cards.append(
        f"""
        <g>
          <rect x="{x}" y="104" width="240" height="96" rx="16" fill="#111827" stroke="#30363D"/>
          <text x="{x + 22}" y="137" fill="#8B949E" font-size="12" font-weight="700" letter-spacing="1.7">{label}</text>
          <text x="{x + 22}" y="178" fill="#F8FAFC" font-size="32" font-weight="800">{value}</text>
        </g>
        """
    )

language_rows = []
start_y = 255
for i, (language, count) in enumerate(top_languages):
    y = start_y + i * 38
    color = palette.get(language, fallback[i % len(fallback)])
    width = max(18, int(420 * count / max_lang))
    language_rows.append(
        f"""
        <g>
          <text x="66" y="{y + 15}" fill="#C9D1D9" font-size="15" font-weight="600">{html.escape(language)}</text>
          <rect x="198" y="{y + 3}" width="420" height="14" rx="7" fill="#21262D"/>
          <rect x="198" y="{y + 3}" width="{width}" height="14" rx="7" fill="{color}"/>
          <text x="633" y="{y + 15}" fill="#8B949E" font-size="13">{count} repo{"s" if count != 1 else ""}</text>
        </g>
        """
    )

if not language_rows:
    language_rows.append(
        '<text x="66" y="276" fill="#8B949E" font-size="15">No primary-language data available.</text>'
    )

svg = f"""<svg width="1200" height="470" viewBox="0 0 1200 470" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="dashboardBg" x1="30" y1="20" x2="1170" y2="450" gradientUnits="userSpaceOnUse">
      <stop stop-color="#0D1117"/>
      <stop offset="1" stop-color="#0B1220"/>
    </linearGradient>
    <linearGradient id="line" x1="54" y1="0" x2="1146" y2="0" gradientUnits="userSpaceOnUse">
      <stop stop-color="#22D3EE"/>
      <stop offset="0.5" stop-color="#8B5CF6"/>
      <stop offset="1" stop-color="#F59E0B"/>
    </linearGradient>
  </defs>

  <rect x="1" y="1" width="1198" height="468" rx="24" fill="url(#dashboardBg)" stroke="#30363D" stroke-width="2"/>
  <rect x="54" y="56" width="1092" height="3" rx="1.5" fill="url(#line)"/>

  <text x="54" y="91" fill="#F8FAFC" font-family="Segoe UI, Inter, Arial, sans-serif" font-size="24" font-weight="800">GitHub pulse</text>
  <text x="1146" y="91" text-anchor="end" fill="#8B949E" font-family="Segoe UI, Inter, Arial, sans-serif" font-size="13">@{esc_owner} · refreshed {refreshed}</text>

  <g font-family="Segoe UI, Inter, Arial, sans-serif">
    {"".join(cards)}

    <text x="54" y="236" fill="#F8FAFC" font-size="18" font-weight="800">Primary languages by repository</text>
    {"".join(language_rows)}

    <g>
      <rect x="735" y="236" width="411" height="184" rx="18" fill="#111827" stroke="#30363D"/>
      <text x="761" y="271" fill="#8B949E" font-size="12" font-weight="700" letter-spacing="1.5">RECENT BUILD SIGNAL</text>
      <text x="761" y="310" fill="#F8FAFC" font-size="24" font-weight="800">{esc_recent}</text>
      <text x="761" y="344" fill="#AAB2BF" font-size="15">Most recently pushed owned repository</text>

      <circle cx="774" cy="386" r="5" fill="#22D3EE"/>
      <text x="790" y="391" fill="#C9D1D9" font-size="14">Live metrics from the GitHub API</text>

      <circle cx="1015" cy="386" r="5" fill="#F59E0B"/>
      <text x="1031" y="391" fill="#C9D1D9" font-size="14">Daily refresh</text>
    </g>
  </g>

  <text x="54" y="446" fill="#6E7681" font-family="Segoe UI, Inter, Arial, sans-serif" font-size="12">Public GitHub data only · generated automatically by this profile repository</text>
</svg>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Wrote {OUT}")
