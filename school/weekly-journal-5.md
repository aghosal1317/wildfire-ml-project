# \hfill Journal Report 5

## \hfill Aneesh Ghosal
\vspace{-0.5em}
\hfill October 26, 2026

\vspace{1em}
\hrule
\vspace{0.5em}

**Research Topic:** I'm studying why evacuation alerts failed in deadly U.S. wildfires (Lahaina 2023 and the Camp Fire 2018). I compare when public awareness spiked in news and social media against the official warning timeline, and will use that to calibrate a simulation estimating how many deaths specific interventions (earlier alerts, working sirens) could have prevented.

**Mid October Goal:** Have all news (GDELT) and Reddit data collected and cleaned, and run burst detection on every source.

**October Goal:** Fill in the official timelines from the Hawaii AG report and Camp Fire reports, measure the difference between public activity and official warnings, write an initial report of what went wrong, and start planning the simulation.


\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (10/26/26-10//26)

### Monday October 26

Watched videos of Lahaina and California wildfires. Understood the extent of the fires through live videos and police body cam footage. Realized how important official reports were to people, especially elder indiviudals, for evacuation. Many of the California wildfire deaths were aged 65+, and didn't think the fires were significant until it was too late.

### Friday October 23

I used the classifier results to see what happened on Reddit during the Lahaina fire. Between 2 and 8 PM, while the town burned, there were almost no fire posts. They only took off around 8 PM, 5 hours after the flare-up. Most early posts were secondhand reports and reposted news, not eyewitness accounts. Local Reddit still beat national news by about 5 hours, but came after the official alerts.

## Timeline

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Analyze data: run burst detection on every source & Done \\
\hline
Today minus 1 week & Get keyword search done; use classifiers to see if they are more useful than keywords & Done \\
\hline
This week & Finish training the two models, evaluate against keywords, diagnose and write initial report & Training and evaluation done; diagnosis started; report not started yet \\
\hline
Today plus 1 week & Verify the Camp Fire timeline with the NIST reports; find when power and cell service failed in West Maui; write initial report & \\
\hline
Today plus 2 weeks & Build the Lahaina failure taxonomy and start planning the simulation & \\
\hline
\end{longtable}

## Reflection

The classifiers improved my results from keyword, but I have to change how I see the project. I expected social media to spread the word faster than official channels, but Reddit was relatively silent during the worst hours, likely because of power and cell service going down. My research question is still held up though, since that is evidence that connunication channels failed, not just the warnings. Next, I want to make a visual for the timeline of the Maui fires, then move onto the California fires to do a similar analysis. After that I will write the official report.

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{fullpage}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---