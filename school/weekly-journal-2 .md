# Journal Report 1

## Aneesh Ghosal

**Research Topic:** State in 1-3 sentences the overall goal of your research project. This should rarely change, but it can when you find you need to modify your scope.

**Mid October Goal:** (What will you have done by 10/15-ish)

**October Goal:** (And by 10/30-ish)


\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (9/30/26-10/5/26)

This daily log summarizes your research for the previous week Sunday to Sunday.

### Wednesday October 7

I am still getting 429 errors. I will try leaving my computer open and have the script fun with caffinate, but I'm not very optomistic that it will even pull data, since the api is giving many errors. 

### Thursday October 8

I ran the scripts at home, PullPush seems to actually be working there, so I got r/California and r/Hawaii data. Seems like the school's wifi is blocking something with PullPush, even though it worked before. 

### Friday October 3

In the notebook, I ran burst detection on each source to find the first hour where activity spiked above the previous 24 hours. 10 of the 12 sources with data show a clear burst. Local Hawaii comments spiked first, much before GDELT. Soon after, r/Maui comments spiked, but again, before GDELT. This is a little promising for my project because it shows that local social media picked up on the fire a few hours before national news did. For camp fire, local posts were too small to find a clear spike.

I need to input official timeline data to measure how far ahead/behind the official warnings were.

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
  - \usepackage{fullpage}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---