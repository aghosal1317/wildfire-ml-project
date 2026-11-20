# \hfill Journal Report 6

## \hfill Aneesh Ghosal
\vspace{-0.5em}
\hfill November 20th, 2026

\vspace{1em}
\hrule
\vspace{0.5em}

**Research Topic:** I'm studying why evacuation alerts failed in deadly U.S. wildfires (Lahaina 2023 and the Camp Fire 2018). I compare when public awareness spiked in news and social media against the official warning timeline, and will use that to calibrate a simulation estimating how many deaths specific interventions (earlier alerts, working sirens) could have prevented.

**October Goal:** Fill in the official timelines from the Hawaii AG report and Camp Fire reports, measure the difference between public activity and official warnings, write an initial report of what went wrong, and start planning the simulation.

**Mid December Goal:** Verify the Camp Fire timeline against the NIST reports, finish the failure taxonomy for both fires, and have a first working version of the Lahaina simulation (agents on a grid of the town, a fire spread model, and an alert module) that I can start calibrating against the real timeline.

\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (11/10/26-11/12/26)

### Tuesday November 10

Wrote the initial report to for the Lahaina wildfire. It goes over my methodology, inclduing comparing official alert timeines against news coverage and Reddit, using burst detection, keyword filtering, machine learning classifiers, and hand coded posts.

It found that public online activity never came before the offciial warnings. In Lahaina, information reached Reddit 2.4-5.2 hours after dispatch recorded each event, while phone and cell service failed around 5PM, and in the Camp Fire a failed alert system left alomst all of the 52000 evacuees without a Code Red notification.

### Thursday November 12

I kept drafting the initial report for the Lahaina wildfire. I thought there were some inconsistencies between what I thought was happening and what the official timelines were showing, so I sorted them out. 

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Verify the Camp Fire timeline with the NIST reports; find when power and cell service failed in West Maui; write initial report & Mostly done. Outage timeline and report draft done; NIST verification not done yet \\
\hline
Today minus 1 week & Build the Lahaina failure taxonomy and start planning the simulation & Partly done. First draft of the taxonomy is in the report; simulation planning not started \\
\hline
This week & Verify the Camp Fire timeline with NIST TN 2252 and TN 2135; fill in the taxonomy rows that need more evidence & Not done. Reviewed and edited the initial report instead \\
\hline
Today plus 1 week & Verify the Camp Fire timeline with NIST TN 2252 and TN 2135; fill in the taxonomy rows that need more evidence & \\
\hline
Today plus 2 weeks & Design the simulation: grid, agents, fire spread, and alert module & \\
\hline
\end{longtable}

## Reflection

This week was a little slower than usual. I focused on reviewing the intial report (written with Claude, so I wanted to make sure everything was consistent with my understanding and results). Reading the whole report helped me see the main story that during the fire, online acitvity came after the offcial warnings, and the phone network failed right when people were in need of it the most. 

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{fullpage}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---