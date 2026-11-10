# \hfill Journal Report 5

## \hfill Aneesh Ghosal
\vspace{-0.5em}
\hfill November 05, 2026

\vspace{1em}
\hrule
\vspace{0.5em}

**Research Topic:** I'm studying why evacuation alerts failed in deadly U.S. wildfires (Lahaina 2023 and the Camp Fire 2018). I compare when public awareness spiked in news and social media against the official warning timeline, and will use that to calibrate a simulation estimating how many deaths specific interventions (earlier alerts, working sirens) could have prevented.

**October Goal:** Fill in the official timelines from the Hawaii AG report and Camp Fire reports, measure the difference between public activity and official warnings, write an initial report of what went wrong, and start planning the simulation.

**Mid December Goal:** Verify the Camp Fire timeline against the NIST reports, finish the failure taxonomy for both fires, and have a first working version of the Lahaina simulation (agents on a grid of the town, a fire spread model, and an alert module) that I can start calibrating against the real timeline.

\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (10/26/26-11/05/26)

### Monday October 26

Watched videos of Lahaina and California wildfires. Understood the extent of the fires through live videos and police body cam footage. Realized how important official reports were to people, especially elder indiviudals, for evacuation. Many of the California wildfire deaths were aged 65+, and didn't think the fires were significant until it was too late.

### Wednesday October 28

I built a timeline fo when power and phone service failed in West Maui using the official FSRI timeline and Hawaiin Electric's and the FCC's reports. Power was out across Lahaina from about 5 AM, before the morning fire started. The fire crews reported no cell service at 5:39 PM, when the fire reached front street and people had to jump in hte ocean. The Wahikuli wireless alert (kind of like an amber alert) went out at 8:46 PM, meaning it went 3 hours after cell service was already gone. I made a figure comparing the outages to Reddit posts. The first local post about the outage didn't come unttil 8:09 PM. 

## Timeline

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Finish training the two models, evaluate against keywords, diagnose and write initial report & Done. SetFit was best at finding fire posts; diagnosis done; report written Oct 28 \\
\hline
Today minus 1 week & Verify the Camp Fire timeline with the NIST reports; find when power and cell service failed in West Maui; write initial report & Mostly done. Outage timeline done; NIST verification and report not done yet \\
\hline
This week & Build the Lahaina failure taxonomy and start planning the simulation & Partly done. Starting to draft taximony; simulation planning not started \\
\hline
Today plus 1 week & Verify the Camp Fire timeline with NIST TN 2252 and TN 2135; fill in the taxonomy rows that need more evidence & \\
\hline
Today plus 2 weeks & Design the simulation: grid, agents, fire spread, and alert module & \\
\hline
\end{longtable}


## Reflection

I mostly met my October goal. I filled in the official timelines, measured how far public activity was from the official warnings for both fires, but couldn't write my entire initial report. I didn't start planning the simulation, and the Camp Fire timeline still has two times I need to verify with the NIST reports.

The outage timeline changed how I understand the Reddit silence. In Lahaina, the phone network went down right when the fire reached town, so the poeple in the most danger couldn't post or get alerts. One of the wireless alerts was sent way after cell service was gone, when many had already died. This supports my research question, because it shows the problem wasn't only that the warnings were late, but also that the methods used for the warnings were faulty. For the simulation, I need to model which channels actually works at each point in time, not just when the alerts are sent. 

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{fullpage}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---