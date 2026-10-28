# \hfill Initial Report: Alert Failures in Two Deadly U.S. Wildfires

## \hfill Aneesh Ghosal
\vspace{-0.5em}
\hfill October 28, 2026

\vspace{1em}
\hrule
\vspace{0.5em}

## Summary

My project asks what in the alert and evacuation process contributed most to deaths in U.S. wildfires, and how much specific changes could have reduced them. I studied two fires, Lahaina (Maui, August 8, 2023) and the Camp Fire (Paradise, California, November 8, 2018), comparing official timelines against news (GDELT) and Reddit using burst detection, a keyword filter, two machine-learning classifiers, and hand-coded posts. In neither fire did public online activity come before the official warnings. In Lahaina, Reddit was nearly silent from 2 to 8 PM while the town burned. Every event I traced reached Reddit 2.4–5.2 hours after police or fire dispatch recorded it, the emergency operations center's logs barely recorded those events, and phone and cell service failed around 5 PM. In the Camp Fire, the link that should have sent the county's CodeRED alerts out as federal phone alerts failed, and only about 7,000 of 52,000 evacuees were notified. Next, I will verify the Camp Fire timeline, finish a failure taxonomy, and plan the simulation.

## 1. Introduction

My research question, from my proposal, is: *across multiple documented U.S. wildfire disasters, what specifically in the alert and evacuation process contributed most to deaths, and how much would specific interventions have reduced casualties?*

In Lahaina, more than 100 people died [VERIFY: exact death count]. As my proposal argues, the danger was known, so this was mainly a failure to warn people who needed to act immediately, not a failure to predict the fire. Many models predict where fires spread; far fewer study why warnings fail.

Official investigations have already documented what happened in each fire, so I'm not redoing them. My project adds three things:

a. **Measuring whether information reached the public:** comparing when events happened, when officials recorded and announced them, and when they appeared in news and social media.

b. **One consistent failure taxonomy across both fires**, so failures can be compared side by side.

c. **Later, a simulation** estimating how many lives specific changes, such as earlier alerts or working sirens, might have saved.

This report covers (a) and a first draft of (b).

## 2. Background

**Lahaina.** The Hawaii Attorney General's investigation was carried out by the Fire Safety Research Institute (FSRI) in three phases. Phase One is a comprehensive timeline, published with a minute-by-minute dataset that I use heavily: 12,140 timestamped entries from dispatch audio, emergency management logs, wireless emergency alerts (WEA), Emergency Alert System (EAS) messages and county social media. Phase Two contains findings and recommendations; I still need to check it for whether the sirens were activated. I haven't used Phase Three yet.

**Camp Fire.** My main source is the Cal OES 2018 Camp Fire After Action Report (AAR), which is much less detailed. Next I'll check NIST Technical Notes 2135 (how the fire spread) and 2252 (notification, evacuation, traffic and refuge areas).

**Related work.** Lever and Arcucci (2022) combined Twitter and satellite data to estimate fire severity in real time, treating social media as a "human sensor network". I use the same idea, but to compare when public awareness emerged against when alerts went out. For simulation, WUI-NITY (Wahlqvist et al., 2021) couples fire spread with traffic, and Pishahang et al. (2024) built a Bayesian agent-based model of the Camp Fire evacuation. Both focus on how people move rather than on the alert chain. A CBS News investigation found at least a dozen U.S. disasters with alert failures in the past decade, so this isn't a one-time problem.

## 3. Data and Methods

### 3.1 Data

- **News (GDELT).** GDELT's search API rate-limited almost every request, so I used its raw 15-minute bulk files instead. They have no rate limit and no 250-article cap: 3,875 Lahaina articles (up from 250) and 1,641 for the Camp Fire. Articles are matched on metadata (URL, title, places, names), not full text.
- **Reddit.** PullPush gave a Reddit-wide keyword search ("Lahaina fire" and similar): 212 posts and 445 comments for Lahaina, 72 and 55 for the Camp Fire. Arctic Shift gave everything posted in local subreddits: r/Hawaii (257 posts, 5,288 comments), r/Maui (439 posts, 6,551 comments) and r/California (276 posts, 3,495 comments). r/Chico had no data for the Camp Fire week.
- **Normal-week baseline.** The same subreddits 7 days before each fire. It shows each subreddit's usual activity (r/Maui had only 177 posts and comments that week, against about 7,000 in the fire week) and gives the classifiers posts guaranteed not to be about the fire.
- **Official timelines.** The FSRI dataset for Lahaina and the Cal OES AAR for the Camp Fire.

### 3.2 Burst detection

I counted posts or articles per hour and compared each hour with the 24 hours before it (not including itself). An hour is a burst if its z-score is 3 or higher. The spread can't drop below normal random noise, and nothing is flagged until there are 6 hours of history. My first version included each hour in its own baseline, which capped the z-score at about 2.04, so real spikes almost never counted. After fixing it, 10 of the 12 sources with data showed a burst.

### 3.3 Filtering: keywords and two classifiers

The local subreddit files contain everything posted, so I first kept posts with words like *fire*, *smoke* or *evacuate*. Keywords miss posts like "Are you still evacuated?", so I also tested two classifiers on the Lahaina data:

- **Zero-shot DeBERTa** needs no training. It judges whether a post implies a sentence like "This text is about a disaster or its aftermath". (My first wording, naming the August 2023 Maui fires, found only 1% of relevant posts.)
- **SetFit** learns from a few labeled examples by fine-tuning a sentence-embedding model on pairs of posts. I added 150 normal-week posts as "not relevant"; without them, it flagged 67% of the fire week as fire-related.

I labeled 277 posts as not relevant or one of 8 categories (warning, eyewitness, secondhand, info request, news or official, help, sympathy, discussion), then split them into 166 training and 111 test posts. The labels were drafted with Claude. I also checked false alarms on 500 held-out normal-week posts.

| | Keyword filter | Zero-shot | SetFit |
|--------------------------------|---------------|---------------|---------------|
| Finding fire posts: F1 (95% range) | 0.85 (0.79–0.90) | 0.89 (0.83–0.94) | **0.91 (0.87–0.96)** |
| False alarms on normal-week posts | **2.6%** | 4.6% | 4.0% |
| Category accuracy (88 relevant test posts) | — | 0.51 | **0.66** |
| Category macro-F1 | — | 0.52 | 0.52 |

: Comparison of the three filtering methods on held-out posts.

SetFit finds fire posts best: 5,655 of the 12,261 fire-week posts, about 2.3 times what the keywords found. Neither model is reliable for categories: zero-shot does better on eyewitness posts (F1 0.63 vs. 0.33), and warnings can't be evaluated (only 3 labeled). Because the labeled sample over-represents keyword matches, these numbers compare the methods with each other, not with the full dataset.

### 3.4 Content and timing

To see *what* people said, I hand-coded the first fire-related local posts on the evening of August 8 (6–10 PM HST). For each event they mentioned, such as Front Street burning or people in the ocean, I compared when police or fire dispatch first recorded it, when the emergency operations center (EOC) or Maui Emergency Management Agency (MEMA) logged it, and when it first appeared on Reddit.

## 4. Results: Lahaina (August 8, 2023)

### 4.1 Official timeline

Lahaina had two fires that day. The 6:37 AM fire was declared contained before the deadly flare-up at 2:55 PM, so I measure lags from 2:55 PM.

| Time (HST) | Event | Channel |
|----------|--------------------------------------------------------|--------------------|
| 6:37 AM | Morning fire reported on Lahainaluna Rd; evacuations nearby at 6:40 | Police door-to-door |
| 9:55 AM | County posts that the fire is 100% contained | Facebook |
| **2:55 PM** | **Fire flares up again (Kuʻialua St)** | |
| 3:07 PM | Police start evacuating homes west of Kuʻialua | Police door-to-door |
| 4:16 PM | **First WEA/EAS for any Lahaina area**, one subdivision (Kelawea Mauka) | WEA + EAS |
| 4:24 PM | Fire jumps the highway toward Front Street | |
| 4:45 PM | County update: bypass closed, "shelter in place encouraged" | Facebook |
| 6:01 PM | About 100 people in the ocean off Front Street | |
| 8:46 PM | WEA for Wahikuli Subdivision | WEA + EAS |

: Lahaina official timeline (FSRI).

I found no record of the outdoor sirens being sounded [VERIFY: confirm in the FSRI Phase Two findings].

### 4.2 The afternoon silence and the evening rise

From 2 to 8 PM, there was almost no fire talk on Reddit: r/Maui had 0 fire-related comments in nearly every hour. This isn't missing data, since r/Hawaii was archived at 20–50 comments an hour all afternoon, just not about the fire. SetFit agrees: 0–3 fire posts per hour, and the few it added beyond the keywords were false alarms. The only warning posted all afternoon was a 3:51 PM repost of an evacuation advisory for Olinda and Piʻiholo, about a *different* fire in Upcountry Maui. Nothing warned about Lahaina.

Around 8 PM, local Reddit reacted: fire-related r/Maui comments rose to 7, 15, then 18 an hour, with a first burst at 8 PM. That is 5.1 hours after the flare-up, 3.7 hours after the first Lahaina WEA, and 2 hours after people were already in the ocean. National news (GDELT) first burst around 1 AM on August 9 and peaked around 10–11 AM. The order was: **fire, official alerts, local Reddit (evening), then Reddit-wide and national news (next morning).**

![Lahaina activity by hour (Hawaii time): local fire-related Reddit (top), Reddit-wide search (middle), and news articles (bottom). Red lines: (1) flare-up 2:55 PM, (2) first Lahaina WEA 4:16 PM, (3) fire jumps the highway 4:24 PM, (4) about 100 people in the ocean 6:01 PM, (5) Wahikuli WEA 8:46 PM.](data/report_lahaina_timeline.png){width=78%}

### 4.3 What the early posts said

From 6 to 10 PM, r/Maui and r/Hawaii had only 29 unique fire-related posts, and just 10 were about Lahaina (most were about the Upcountry and Kihei fires).

| Type of post | All fires | Lahaina only |
|--------------------------------------------------|----------|-------------|
| Warning telling people to act | 0 | 0 |
| Eyewitness | 7 | 2 |
| Secondhand ("I hear…", photos from a friend) | 6 | 4 |
| Asking for information (family, homes, sources) | 8 | 1 |
| Repost of news or an official alert | 5 | 1 |
| Reaction or sympathy | 3 | 2 |

: Hand-coded fire-related posts, 6–10 PM HST, August 8.

No one posted a warning. Lahaina posts were mostly secondhand and after the fact ("I hear Front Street Apartments have burned"), and eyewitnesses posted only after escaping. A hotel guest on Front Street posted at 9:39 PM about smelling smoke around 5 PM, watching the fire jump between streets, and then sitting in traffic for hours with no power at the gas stations. Others asked where to find reliable updates at all. Over the whole week, the classifier shows the same start (mostly secondhand reports and reposts), then a shift toward discussion, sympathy and offers of help.

![Lahaina fire-related posts per 3 hours (top) and share in each information category (bottom), from SetFit. Grey windows had fewer than 20 posts. Categories are broad trends only.](data/report_information_categories.png){width=72%}

### 4.4 Event timing: dispatch, EOC and Reddit

| Event | First dispatch record (HST) | EOC/MEMA log | First on Reddit | Reddit delay |
|-----------------------------------|--------------|---------------|-------------|-----------|
| Fire in the Front St / Waineʻe neighborhood | 4:24 PM | none on Aug 8 | 7:57 PM | 3.6 h |
| Island Grocery burning | 5:21 PM | none on Aug 8 | 7:57 PM | 2.6 h |
| Front Street Apartments burning | 5:34 PM | none on Aug 8 | 7:57 PM | 2.4 h |
| Outlets of Maui on fire | 5:44 PM | none on Aug 8 | 8:35 PM | 2.8 h |
| People in the ocean | 5:44 PM | none on Aug 8 | 10:58 PM | 5.2 h |
| Coast Guard responding | 6:07 PM | none on Aug 8 | 9:50 PM | 3.7 h |

: When each Lahaina event appeared in dispatch records, EOC logs, and Reddit.

Every event reached Reddit **2.4 to 5.2 hours after** dispatch recorded it. Posts beat the EOC logs only because those logs don't mention these town-level events at all on August 8. At 6:40 PM, the federal fire-assistance request even recorded "0 structures involved", more than two hours after dispatch began reporting burning homes and businesses. "Not logged" doesn't prove the EOC didn't know, since information may have come by phone or been redacted, but it suggests a gap between responders on the ground and the operations center.

### 4.5 Phones and power

The FSRI timeline shows communications failing at the worst time. At 4:22 PM, police dispatch said "our phones are down" (unclear whether only the station's landlines). Around 5:00 PM, Hawaiian Telcom lost connectivity to its Lahaina and Napili central offices, which carry landlines and internet (reported to the EOC at 6:59 PM). At 5:33 PM, the fire-assistance request noted spotty cell service and Hawaiian Tel and Spectrum service down; at 5:39 PM, fire crews in Lahaina had no cell service. Power was already out: MEMA logged about 7,000 customers without power at 5:38 AM, and at 5:02 PM Hawaiian Electric warned of an extended outage. This helps explain the *evening* silence, but not the 2:55–5 PM silence, when phones may still have worked. I need exact outage times to test this.

## 5. Results: Camp Fire (November 8, 2018)

| Time (PST) | Event |
|------------|----------------------------------------------------------------------------|
| 6:33 AM | First reports of fire near Poe Creek Dam |
| 7:13 AM | First evacuation notice (Pulga) |
| by 8:00 AM | Concow and Paradise notified [VERIFY: other sources give 7:54 or 8:03 AM for Paradise; check NIST TN 2252] |
| about 8:30 AM | Fire begins consuming Paradise [VERIFY: NIST TN 2135] |

: Camp Fire official timeline (Cal OES AAR unless noted).

The AAR reports that the link sending CodeRED messages out as federal phone alerts (IPAWS) **failed**, and that only about **7,000 of the 52,000 evacuees** received a CodeRED notification. Public activity started 2–3 hours after the first reports: fire-related r/California comments and news coverage both began around 9–10 AM, while Paradise was burning. The local signal is thin, with fewer than 10 Camp Fire comments an hour (too few for a burst; highest z-score 1.75). r/California covers the whole state, and the Woolsey and Hill fires started in Southern California the same day, so I only counted posts naming the Camp Fire or nearby places. r/Chico, the closest local subreddit, has no data.

## 6. Initial Failure Taxonomy

My first draft across both fires. Rows marked **needs evidence** can't be fully supported yet.

| Fire | What failed | When (local) | Channel | Evidence (source) |
|--------|------------------------|----------------|--------------|------------------------------------------|
| Lahaina | Fire announced as contained, then flared up | 9:55 AM post; flare-up 2:55 PM | Facebook | County said 100% contained; fire re-ignited 5 hours later (FSRI timeline) |
| Lahaina | Wireless alerts late and narrow | First Lahaina WEA 4:16 PM; Wahikuli 8:46 PM | WEA + EAS | 81 minutes after the flare-up, for one subdivision (FSRI timeline) |
| Lahaina | Evacuation depended on door-to-door police | 3:07 PM onward | Police door-to-door | Only channel used before 4:16 PM (FSRI timeline) |
| Lahaina | Conflicting public message | 4:45 PM | Facebook | "Shelter in place encouraged" after the fire jumped the highway at 4:24 PM (FSRI timeline) |
| Lahaina | Outdoor sirens not sounded (**needs evidence**) | — | Sirens | No record in the timeline [VERIFY] (FSRI Phase Two) |
| Lahaina | Phone and cell networks failed (**needs exact times**) | about 4:22–5:39 PM | Landline, cell, internet | Exchange lost about 5 PM; no cell service 5:39 PM; power out since early morning (FSRI timeline) |
| Lahaina | EOC situational awareness gap (**needs evidence**) | Evening of Aug 8 | EOC logs | Town-level events not logged; "0 structures involved" at 6:40 PM (FSRI timeline; my timing comparison) |
| Lahaina | Information reached the public late | 2.4–5.2 h after dispatch | Reddit (proxy for the wider public) | No warnings posted; eyewitnesses posted after escaping (Hand-coded posts; timing comparison) |
| Camp Fire | Alert integration failed | Nov 8 | CodeRED to IPAWS phone alerts | CodeRED messages didn't go out as federal alerts (Cal OES AAR) |
| Camp Fire | Most evacuees not notified | Nov 8 | CodeRED | About 7,000 of 52,000 evacuees notified (Cal OES AAR) |
| Camp Fire | Notice close to fire arrival (**needs evidence**) | Paradise notified by 8:00 AM; fire about 8:30 AM | Evacuation notices | Both times [VERIFY] with NIST (Cal OES AAR; NIST TN 2135 / 2252) |

: Initial failure taxonomy for both fires.

Both fires share a pattern: official alerts that were late, narrow or never delivered, with backup channels (door-to-door, phones, social media) unable to make up the difference.

## 7. Discussion

I started out hoping social media might work as an early warning, spreading news faster than official channels. In these fires, it didn't. In Lahaina, nothing public came before the fire or the official alerts, and no one posted a warning about Lahaina at all.

Instead, Lahaina's information channels went dark at the same time the alerts failed. Power had been out since early morning, the phone exchanges dropped around 5 PM, and cell service was gone by 5:39 PM, just as the fire reached Front Street. The people in the most danger mostly couldn't post, and the eyewitnesses I found had already escaped. The EOC logs show the same gap on the official side.

Local Reddit did lead national news in Lahaina, by about 5 hours, but not in the Camp Fire, where r/California and news coverage started together around 9–10 AM. (My README's headline says local Reddit led in both fires; the detailed Camp Fire results don't support that, so I'll correct it.)

So I'm reframing what Reddit measures. It doesn't show what people in danger knew, since most of them weren't posting. It shows **whether and when information reached the wider public**: friends, family, visitors and the rest of the island. By that measure, news of Lahaina reached the public hours late and mostly secondhand.

## 8. Limitations

- **Only two fires**, so the findings are descriptive and may not generalize.
- **Reddit isn't awareness.** Many affected people never posted, or used Facebook, texts or calls instead.
- **Outages confound the silence.** After about 5 PM, few posts may mean broken phones, not lack of awareness, and I don't have exact outage times.
- **Archive gaps.** r/Chico has no data, the Reddit-wide files end about 4 hours into the last day, and Reddit-wide search only includes posts matching the keywords.
- **Hand labels** were drafted with Claude and not yet fully reviewed.
- **Category labels are unreliable** for eyewitness posts and can't be evaluated for warnings, so they're broad trends only.
- **GDELT matching** uses metadata, not full text.
- **Camp Fire times** for the Paradise notice and fire arrival are unverified.

## 9. Next Steps

1. **Outage timing table:** pin down when power, landlines and cell service failed in West Maui, to test whether they line up with the Reddit silence.
2. **Verify the Camp Fire timeline** with NIST TN 2252 and TN 2135, and confirm the siren question in FSRI Phase Two.
3. **Finish the taxonomy:** fill the "needs evidence" rows and add casualty information. Also review the hand labels, label more eyewitness posts and warnings, and run the classifier on the Camp Fire.
4. **Plan the simulation:** as in my proposal, agents with mobility, distance to an exit and access to each alert channel, on a grid of the community, with a fire spread model and an alert module. I'll calibrate it on Lahaina's timeline, then vary alert delay and siren failure to see how simulated deaths change.

## References

Cal OES (California Governor's Office of Emergency Services). *2018 Camp Fire After Action Report.* https://www.caloes.ca.gov/wp-content/uploads/Preparedness/Documents/FINAL-AAR-2018-Camp-Fire-508-Clean-Copy-11.17.25.pdf

CBS News. (n.d.). Investigation into U.S. disasters where officials failed to issue timely emergency alerts. https://www.cbsnews.com

Fire Safety Research Institute, for the Hawaii Department of the Attorney General. (2024). *Lahaina Fire Comprehensive Timeline Report* (Phase One) and minute-by-minute timeline dataset. https://ag.hawaii.gov/maui-wildfire-investigation-resources-page/

Fire Safety Research Institute, for the Hawaii Department of the Attorney General. *Lahaina Fire Incident Analysis Report* (Phase Two): findings and recommendations. Same resources page.

GDELT Project. Global Knowledge Graph 15-minute bulk files.

Lever, J., & Arcucci, R. (2022). Sentimental wildfire: a social-physics machine learning model for wildfire nowcasting. *Journal of Computational Social Science, 5*(2), 1427–1465. https://doi.org/10.1007/s42001-022-00174-8

Models and archives: Arctic Shift and PullPush (Reddit archives); `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` (zero-shot classifier); `sentence-transformers/paraphrase-mpnet-base-v2` with the SetFit library (few-shot classifier).

National Institute of Standards and Technology. *Technical Note 2135: A case study of the Camp Fire — fire progression timeline.*

National Institute of Standards and Technology. *Technical Note 2252: A case study of the Camp Fire — notification, evacuation, traffic, and temporary refuge areas.*

Pishahang, M., Ruiz-Tagle, A., Ramos, M. A., Droguett, E. L., & Mosleh, A. (2024). A Bayesian agent-based model and software for wildfire safe evacuation planning and management. *Proceedings of the Institution of Mechanical Engineers, Part O: Journal of Risk and Reliability.* https://doi.org/10.1177/1748006X241259215

Wahlqvist, J., Ronchi, E., Gwynne, S. M. V., et al. (2021). The simulation of wildland-urban interface fire evacuation: The WUI-NITY platform. *Safety Science, 136*, 105145. https://doi.org/10.1016/j.ssci.2020.105145

---
geometry: margin=1in, letterpaper
header-includes:
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \DeclareUnicodeCharacter{02BB}{\textquoteleft}
  - \usepackage{float}
  - \floatplacement{figure}{H}
---
