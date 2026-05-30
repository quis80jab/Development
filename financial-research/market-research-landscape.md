# Market Research — Automated Aircraft Inspection, MRO & the Oyster/KAAF Thesis

**Prepared:** 2026-05-30 · **Author:** Ben (ben@arachnidsys.com)
**Purpose:** Situate the Oyster Aviation (KAAF) idea inside the broader market — competitors,
adjacent industries, comparable M&A, and the structural demand drivers behind Arachnid's ATLAS.

---

## 1. Market sizing (the demand backdrop)

| Market | Size (now) | Forecast | CAGR | Source |
|---|---|---|---|---|
| Global MRO (maintenance, repair, overhaul) | ~$78B (2023) | growing | — | MarketsandMarkets |
| Drone inspection (all verticals) | ~$13.6B (2026) | $25.8B (2030) | 17.3% | sector reports |
| Robotics & drone-based **NDT** | ~$1.24B (2025) | $2.52B (2030) | 15.2% | Mordor Intelligence |
| NDT robotic inspection (broad) | $15.9B (2023) | $44.1B (2032) | 12.0% | Straits Research |
| Digital MRO | ~$0.9B (2023) | $2.0B (2030) | 13.0% | MarketsandMarkets |
| Automated stationary NDT systems | $767M (2025) | $1.20B (2030) | 9.3% | MarketsandMarkets |

**Takeaway:** Arachnid plays in a **double-digit-CAGR niche (robotic/drone NDT)** riding on a
huge ($78B) MRO base. ~68% of aerospace manufacturers reportedly already integrate some
automated NDT — adoption is past "if," now "which vendor / how fast."

---

## 2. The structural driver: the A&P mechanic shortage

This is the single biggest tailwind and the reason the Oyster angle is even interesting.

- **Boeing 2025 outlook:** ~**710,000 new maintenance technicians** needed globally over 20 yrs.
- Workforce is aging out — large share of certificated A&Ps are baby-boomers retiring faster
  than schools graduate replacements; **~1/3 of AMT school seats sit unfilled**.
- US BLS: only ~5% growth 2024–2034, ~13,100 openings/yr — **supply cannot meet demand**.
- Result: MRO backlogs, aircraft-on-ground time, and rising labor cost ($120k+ at majors).

**Strategic read:** automation isn't replacing a healthy labor pool — it's filling a *structural
gap*. A company that owns **both** the automation (ATLAS) **and** scarce certificated labor
(an A&P/IA shop like Oyster) is positioned at exactly the chokepoint. That is the real thesis
behind the Oyster idea, even though the shop itself is tiny.

---

## 3. Competitive landscape — automated aircraft inspection

| Company | Country | Approach | Status / differentiator | vs. Arachnid ATLAS |
|---|---|---|---|---|
| **Donecle** | France | Autonomous drones + AI image analysis | 40+ drones, 15 countries; **Airbus, Boeing, EASA, FAA** approvals; raised €10M (Apr 2026); customers United, LATAM, DHL, Lufthansa, French AF, RAF | Most mature commercial competitor. Visual/paint/lightning/placard focus — **optical**, not multi-modal NDT |
| **Mainblades** | Netherlands | "Drone-as-a-tool" + LiDAR nav | Full narrowbody visual inspection ~2 hr; first EU outdoor automated commercial inspection (2021) | Visual/LiDAR; lighter sensor stack than ATLAS |
| **Apellix** | Jacksonville, FL | Contact UAVs w/ robotic arm — **ultrasonic (UT)**, dry-film thickness, gas | Brings true NDT (UT) to drones; hazardous-environment focus | Closest on *contact NDT*; ATLAS claims broader 6-modality fusion |
| **Lufthansa Technik** | Germany | Crawling/clinging robots — **MORFI** (thermographic crack detect to 1mm), **CAIRE** (CFRP repair) | In-house MRO giant building its own robots | Incumbent MRO doing it internally — both competitor and potential customer/channel |
| **Arachnid (ATLAS)** | US | Autonomous multi-sensor robot, **6 fused modalities** (hyperspectral, LWIR, LiDAR, profilometry, radar-NDT, polarimetric RGB), edge Jetson Orin, ITAR/air-gapped | Pilots w/ Lockheed, GDIT; NASA KSC, AFRL, DIU; defense-first | **Differentiated on sensor fusion + defense/ITAR posture**; less commercial-certified than Donecle |

**Positioning read:** The commercial-airline lane is getting crowded and is being won on
**certifications** (Donecle's Airbus/Boeing/EASA/FAA stack is a moat). Arachnid's defensible
wedge is **defense + multi-spectral subsurface/structural NDT + air-gapped edge** — a lane the
European optical-drone players don't serve well. Strategy should lean **into** that wedge, not
chase Donecle on commercial visual inspection.

---

## 4. Comparable M&A — vertical integration is the dominant pattern

The market is consolidating exactly along the "own the certified capability" logic:

- **AAR Corp → Aircraft Reconfig Technologies** ($35M, 2025) — buying **engineering &
  certification capability** + recurring revenue. Most relevant comp to the Oyster thesis.
- **AxioAero Group → Airway Aerospace** (2025) — Florida FAA/EASA/CAA repair station; 2nd buy
  after Aviation Concepts (Jan 2024). A roll-up of certified repair stations.
- **AE Industrial Partners → Air Transport Components** — PE building an MRO platform.
- **Ronin Equity Partners →** award-winning Part 145 repair station — PE entering component MRO.
- **ST Engineering** — serial acquirer internalizing component mfg/logistics into a vertically
  integrated MRO powerhouse.
- **OEM trend:** OEMs buying/building MRO to capture aftermarket and control data/lifecycle.

**Takeaway:** Buying small certified repair stations to gain **certification authority,
recurring aftermarket revenue, and data access** is a proven, active playbook (PE, OEMs, and
MRO majors all doing it). Oyster would be a *micro* version of this — the logic is sound at
scale; the question is whether it's worth Arachnid's attention at GA-shop scale.

---

## 5. Adjacent industry: airfields as autonomy/UAS test infrastructure

KAAF's value as a **non-towered, 3-runway, near-empty county field** mirrors how the autonomy
industry secures test environments:

- **FAA UAS Test Sites** (7 designated; +2 added 2026) — e.g., **NY/Griffiss**, **Northern
  Plains (ND)**, **Pendleton UAS Range (OR)** (14,000 sq mi of approved airspace).
- **Reliable Robotics** runs detect-and-avoid flight tests at **Hollister Municipal** (small
  airport) under FAA contract.
- **Idaho National Laboratory**, **NASA** (autonomous air-taxi research) run dedicated UAS test
  programs.
- USAF investing in autonomous cargo aircraft ($17.4M award noted in trade press).

**Takeaway:** Companies routinely anchor autonomy R&D at quiet regional/municipal fields. A
foothold at KAAF would give Arachnid a captive, low-congestion test environment of the same
character — useful for ATLAS ground robotics *and* any future airborne/UAS sensing work, beyond
just the maintenance-shop angle.

---

## 6. Synthesis — how Oyster/KAAF fits the market

1. **Demand is real and structural** (A&P shortage + $78B MRO base + double-digit NDT-automation
   CAGR). Arachnid is in the right market.
2. **Competition is bifurcating:** crowded, certification-gated commercial-visual lane (Donecle,
   Mainblades) vs. Arachnid's defensible defense/multi-spectral/edge wedge. Protect the wedge.
3. **Vertical integration is the proven M&A playbook** — but the active comps are $35M+ Part 145
   stations and PE roll-ups, not $130/hr piston-GA shops. Oyster is *strategically analogous but
   financially sub-scale*.
4. **The KAAF airfield, not the shop, may be the asset** — fits the well-established pattern of
   anchoring autonomy testing at quiet regional fields.
5. **Decision frame unchanged:** pursue Oyster only as a cheap *capability/test-bed* play
   (certification on-ramp + captive aircraft + data + airfield access). Do **not** justify it as
   a financial MRO acquisition — the comps that work are an order of magnitude larger.

---

## Sources
- Donecle — site / funding: https://www.donecle.com/ · https://dronelife.com/2026/04/16/donecle-raises-e10-million-to-expand-drone-based-aircraft-inspection-platform/
- Mainblades / drone inspection landscape — Aviation Week: https://aviationweek.com/mro/emerging-technologies/aircraft-inspections-drones-accelerate-toward-next-evolution
- Apellix — CB Insights: https://www.cbinsights.com/company/apellix/alternatives-competitors
- Lufthansa Technik MORFI / CAIRE — RAeS: https://www.aerosociety.com/news/flying-clinging-and-crawling-using-robots-in-mro/ · https://www.lufthansa-technik.com/en/caire-repair-robot
- Robotics & drone-based NDT market — Mordor: https://www.mordorintelligence.com/industry-reports/robotics-and-drone-based-ndt-market
- NDT robotic inspection market — Straits: https://straitsresearch.com/report/ndt-robotic-inspection-market
- Digital MRO market — MarketsandMarkets: https://www.marketsandmarkets.com/Market-Reports/digital-mro-market-165029525.html
- A&P shortage — Boeing Pilot & Technician Outlook: https://www.boeing.com/commercial/market/pilot-technician-outlook
- A&P shortage — Aviation Week: https://aviationweek.com/mro/workforce-training/aircraft-mechanic-shortage-real-it-reshaping-aviation-careers-nationwide
- AAR → Aircraft Reconfig Technologies: https://www.aarcorp.com/en/newsroom/press-releases/2025/aar-to-acquire-aircraft-reconfig-technologies-expanding-its-engineering-and-certification-capabilities-and-creating-additional-revenue-streams/
- AxioAero → Airway Aerospace: https://www.eplaneai.com/news/axioaero-group-acquires-airway-aerospace
- AE Industrial Partners → ATC: https://www.aeroequity.com/ae-industrial-partners-establishes-aerospace-mro-services-platform-with-investment-in-air-transport-components/
- Vertical integration in MRO (trend): https://interama.org/vertical-integration-in-mro-a-strategic-shift-in-the-aerospace-industry/
- FAA UAS Test Sites: https://www.faa.gov/uas/programs_partnerships/test_sites/locations · Pendleton: https://www.pendletonuasrange.com/
- Reliable Robotics DAA tests near airports — AIN: https://www.ainonline.com/aviation-news/futureflight/2026-04-08/reliable-completes-detect-and-avoid-tests-near-airports
