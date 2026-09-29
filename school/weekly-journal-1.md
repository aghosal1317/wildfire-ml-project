# \hfill Journal Report 1

## \hfill Aneesh Ghosal
\vspace{-0.5em}
\hfill October 6, 2026

\vspace{1em}
\hrule
\vspace{0.5em}

**Research Topic:** State in 1-3 sentences the overall goal of your research project. This should rarely change, but it can when you find you need to modify your scope.

**Mid October Goal:** Have Reddit and GDELP data ready for analysis.

**October Goal:** Diagnose what went wrong in the Laitia fires, and start planning simulation.


\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (9/30/26-10/5/26)

This daily log summarizes your research for the previous week Sunday to Sunday.

### Tuesday September 29

Today I worked on getting the GDELT project data collection running reliably. The API was giving HTTP 429 (rate limit) errors on pretty much every request. GDELT docs said this was for all users to prevent congestion, not a fixed quota. I added logic to try the API, then wait a few seconds (retry with backoff logic), capped how long the retries go for, and reduced the total number of requests by increasing timings between requests. This fix is kind of working, some requests that failed before are recovering after a few tries, but the total run is taking a while because of how much data there is and waiting between requests. I will let it run, and next class will be able to start analyzing the data.
### Friday October 3

Today I wrote an Chrome Extension that reminds me to meditate. Details..

### Saturday October 4

If you work outside of school time, include it in your journal as well. In general, absence from school does not excuse you from research that day -- I expect you'll make it up a different day that week if possible.

## Timeline

(in latex, use double backslash to separate rows and ampersand for columns. )

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Reminder of your previous goal & Did you meet the goal? (i.e. Done or Not Done) \\
\hline
Today minus 1 week &  & Maybe say if you modified it, etc. \\
\hline
This week & State your goal to be completed at this time & T \\
\hline
Today plus 1 week &  & blank \\
\hline
Today plus 2 weeks &  & blank \\
\hline
\end{longtable}

## Reflection

A detailed person accounting of how this week went, how your project is going, description of successes and failures. If you
need(ed) to change goals, or refocus your project, explain it here. If you have specific questions or needs, you can list them here.
This is a good place to include photos, diagrams, screenshots, code, etc. if it's especially relevant.

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---