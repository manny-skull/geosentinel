# 🌐 GeoSentinel 2.0

**AI-Powered Global Disease Surveillance Network**

Real-time disease outbreak monitoring using open-source intelligence (OSINT). Replacing expensive, slow clinic-based surveillance with automated multi-source signal detection.

<img src="https://img.shields.io/badge/signals-live-brightgreen" alt="Live"> <img src="https://img.shields.io/badge/sources-5-blue" alt="Sources"> <img src="https://img.shields.io/badge/updates-every%2030%20min-orange" alt="Updates">

## 🛰️ Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| 🏥 **WHO** | Disease Outbreak News API | Official alerts, global |
| 📰 **News** | Brave Search (CDC, Reuters, Al Jazeera...) | Breaking outbreaks |
| 𝕏 **Twitter/X** | Real-time social signals | Traveler reports, early detection |
| 💬 **Reddit** | Community reports | Travel health experiences |
| 📈 **Google Trends** | Search trend anomalies | Population-level signals |

## 🔬 Features

- **Real-time scanning** — automated every 30 minutes via GitHub Actions
- **Anomaly detection** — historical baseline comparison flags unusual spikes
- **Traveler signal detection** — NLP patterns identify "came back sick from..." reports
- **Flight risk modeling** — maps potential disease spread via air routes
- **Interactive map** — Leaflet-based with severity-coded markers
- **Multi-severity scoring** — 1-10 scale: critical, high, moderate, low
- **Source-filtered views** — filter by WHO, news, Twitter, Reddit, or Trends

## 🏗️ Architecture

```
GitHub Actions (cron 30 min)
    → scanner_v2.py (Python)
        → WHO API + Brave Search + Twitter + Google Trends
        → NLP disease detection + geocoding + anomaly scoring
        → signals.json
    → GitHub Pages (static deploy)
        → index.html (Leaflet map + dashboard)
```

**Zero infrastructure cost.** Runs entirely on GitHub Actions + Pages.

## 🚀 Deployment

This site auto-deploys via GitHub Pages. Every 30 minutes:
1. Scanner collects signals from 5 sources
2. Processes, deduplicates, scores, and geocodes
3. Commits `signals.json` to repo
4. GitHub Pages serves the updated dashboard

## 📊 Signal Processing Pipeline

1. **Collection** — parallel queries across 5 source APIs
2. **Disease Detection** — regex + NLP matching against 30+ disease patterns
3. **Geocoding** — 100+ country/city database with region classification
4. **Severity Scoring** — base disease severity + modifiers (deaths, outbreak scale, traveler)
5. **Anomaly Detection** — 2× historical baseline comparison
6. **Deduplication** — hash-based + location clustering
7. **Flight Risk** — IATA hub mapping for affected countries

## ⚕️ Background

The original [GeoSentinel](https://www.istm.org/geosentinel) is a WHO/CDC/ISTM clinic-based surveillance network — 70 clinics worldwide, slow reporting, limited coverage. 

**GeoSentinel 2.0** replaces this with AI-powered OSINT: faster, broader, free, and available to everyone.

## 📜 License

MIT — Use freely. Attribution appreciated.

---

*Built with 🪁 by [Kite](https://github.com/acuestamd)*
