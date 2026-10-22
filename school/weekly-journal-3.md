# \hfill Journal Report 3

## \hfill Aneesh Ghosal
\vspace{-0.5em}
\hfill October 20, 2026

\vspace{1em}
\hrule
\vspace{0.5em}

**Research Topic:** I'm studying why evacuation alerts failed in deadly U.S. wildfires (Lahaina 2023 and the Camp Fire 2018). I compare when public awareness spiked in news and social media against the official warning timeline, and will use that to calibrate a simulation estimating how many deaths specific interventions (earlier alerts, working sirens) could have prevented.

**Mid October Goal:** Have all news (GDELT) and Reddit data collected and cleaned, and run burst detection on every source.

**October Goal:** Fill in the official timelines from the Hawaii AG report and Camp Fire reports, measure the difference between public activity and official warnings, write an initial report of what went wrong, and start planning the simulation.


\vspace{1em}
\hrule
\vspace{1em}

## Daily Log (10/13/26-10/20/26)

### Wednesday October 14

I worked on getting the key-word search in. There were two portions to this: local reddit and reddit wide key word search. Local reddit pulls from specific subreddits, trying to find words like "fire" or "smoke" to get comments and posts. Reddit wide search was all subreddits, with more specific key words, like "Lahaina fire." After I got and filtered all the data, I made a new, clearer graph. The result was that the social media posts, in both data types, peak before GDELT. 

### Friday October 16

Dr White suggested trying a classifier instead of only keywords, so I tested two free machine learning models against the keyword filter. First, I labeled 277 posts (with the help of Claude) if they were relevant or not, then split them into a training and test set. The first model was a zero shot DeBERTa model, which didn't need training. It just checked whether a post "implies" a sentence like "this text is about a disaster." The second was SetFit, which learns from the small number of labeled examples. I also downloaded an extra normal week on the same subreddits the before the fire, to give me a baseline I could compare to. 

## Timeline

\begin{longtable}{|p{3cm}|p{6cm}|p{6cm}|}
\hline
\textbf{Date} & \textbf{Goal} & \textbf{Met?} \\
\hline
Today minus 2 weeks & Fix GDELT errors, pull California and Hawaii data & Done. Switched GDELT to bulk files; got r/Hawaii, r/Maui, r/California from Arctic Shift \\
\hline
Today minus 1 week &  Analyze data: run burst detection on every source & Done. Found trends of reddit before GDELT\\
\hline
This week & Get keywords search done; use classifiers to see if it is more useful than keywords & Done. Found same trends as before\\
\hline
Today plus 1 week & Finish training the two free models, evaluate against keywords, diagnose and write intitial report & \\
\hline
Today plus 2 weeks & Continue writing official report & \\
\hline
\end{longtable}

## Reflection

This week, filtering out keywords was very important because it just further confirmed my conclusions from last week: reddit data came before GDELT. This is promising, and I think after the classification, I will see similar trends. They do come after the official emergency call, which is kind of to be expected, but that doesn't necessarily break the project. I now just have to kind of focus on how social media can get the word spread faster than actual news outlets, just not the government. I will continue analysis after the classifier trains next week.


![Trends for Lahaina](data/reddit_data.png)

---
geometry: margin=0.5in, letterpaper
header-includes:
  - \usepackage{fullpage}
  - \usepackage{booktabs}
  - \usepackage{longtable}
  - \thispagestyle{empty}
---