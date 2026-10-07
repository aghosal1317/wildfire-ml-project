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

### Thursday October 1

Today I reran the data collection and made a new GitHub repository for my work while waiting. I included the important things, like data collection scripts, the new CSVs, and an initial jupyter notebook. I also noticed that the LaTex to PDF wasn't working well, so I reinstalled the packages, including one that accounts for fullpage.sty. The Reddit collection now works past the 100 row limit. GDELT still did not finish for Lahaina nor camp fire, so I need to retry next time (I think I shut my computer too soon). PullPush is limited on some subreddits like r/Hawaii and r/California, but next time I will rerun these subreddits.

## Timeline

(in latex, use double backslash to separate rows and ampersand for columns. )

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Find websites with social media data I could use & Done \\
\hline
Today minus 1 week & Pull social media data & Not fully done \\
\hline
This week & Pull social media data & Partially done, some errors in data and I want to pull more eventually \\
\hline
Today plus 1 week & Fix errors with GDELT running, pull california/hawaii data &  \\
\hline
Today plus 2 weeks & Analyze data and make initial report of what went wrong & blank \\
\hline
\end{longtable}

## Reflection

Right now I am still trying to just pull all the data I need to make an initial conclusion of what went wrong in some of these wildfires. It takes a while to run the scripts that pull the data, so while I wait, I will look into more research articles that may be relevant to my project. I also might need to look into where I can get more data, since each source, other than GDELT, is giving me ~200 entries.

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---