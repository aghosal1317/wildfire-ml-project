# Journal Report 2

## Aneesh Ghosal

**Research Topic:** I'm studying why evacuation alerts failed in deadly U.S. wildfires (Lahaina 2023 and the Camp Fire 2018). I compare when public awareness spiked in news and social media against the official warning timeline, and will use that to calibrate a simulation estimating how many deaths specific interventions (earlier alerts, working sirens) could have prevented.

**Mid October Goal:** Have all news (GDELT) and Reddit data collected and cleaned, and run burst detection on every source.

**October Goal:** Fill in the official timelines from the Hawaii AG report and Camp Fire reports, measure the difference between public activity and official warnings, write an initial report of what went wrong, and start planning the simulation.


\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (10/4/26-10/10/26)

### Wednesday October 7

I was still getting 429 errors from the Global Database of Events, Language, and Tone (GDELT) API, even with long waits between the requests. I looked into it, and found GDELT's limit is stricter than the one request every 5 seconds. After one 429, it is blocked for over a minute, so retrying so soon doesn't actually help. Instead, I switched to GDELT's raw bulk files, which have to limit. The script downloads each file but only keeps articles about each fire. This took me from 250 articles to now 3875. 


### Thursday October 8

PullPush started blocking all script requests with a Cloudflare bot check (HTTP 403), so I switched to subreddit specific data in Artic Shift instead, a different Reddit source. What I'm noticing is that it works on my home wifi, but is blocked at school. At home, I got r/Hawaii and r/Maui. I also set up a log so I could see if there were any errors in collection, it didn't look like there were any.

### Friday October 9

For Lahaina, local r/Hawaii comments spiked first (Aug 8, 18:00 UTC), then r/Maui comments (Aug 9, 06:00 UTC), both before national news in GDELT (Aug 9, 11:00 UTC). This is promising because it suggests local social media picked up on the fire hours before national news. For the Camp Fire, r/California comments show a burst, but r/California posts and the Reddit-wide posts were just under the threshold.

One caution: the local subreddit data is everything posted there, not just fire posts, so some early bursts might just be normal morning activity. I need to add a keyword filter (fire, evacuate, smoke, etc.) to check this. I also set up a notebook section for the official timeline, which converts local times to UTC and computes the lag between each warning and each source's first burst.

## Timeline

(in latex, use double backslash to separate rows and ampersand for columns. )

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Pull social media data & Partially done; fixed in the following week \\
\hline
Today minus 1 week & Fix GDELT errors, pull California and Hawaii data & Done. Switched GDELT to bulk files; got r/Hawaii, r/Maui, r/California from Arctic Shift \\
\hline
This week & Analyze data: run burst detection on every source & Done \\
\hline
Today plus 1 week & Fill in official timelines from the AG report and Camp Fire reports; add keyword filter to local subreddit data; compute lag table & \\
\hline
Today plus 2 weeks & Write initial report of what went wrong in each fire and start planning the simulation & \\
\hline
\end{longtable}

## Reflection

This week was mostly about data sources and how to get around their limits. The GDELT API was kind of unusable because of all their rate limits, so switching to the bulk files gave me a lot more data than the API probably could have. PullPush also getting blocked was annoying, but Arctic Shift was able to give me the data I needed. It needs to be run at home though, school wifi blocks it.

The takeaway from this week is that I need to filter my data out, the local subreddit data includes unrelated posts. That means the screenshot of the graph does NOT tell the full story right now.

Next, I need to read the Hawaii AG report and Camp Fire reports to build their timelines (ignition, first warning, etc.), so I can compare my (filtered) results.

![alt text](data/lahaina-bursts.png)

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{fullpage}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---