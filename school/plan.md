# Wildfire Spread and Response-Gap Prediction: 17-Week Project Timeline

 
## Track 1: Fire spread and population exposure
 
**Research question:** Given a wildfire's starting location and local conditions, how far and fast will it spread, and how many people fall in its path?
 
| Weeks | Phase | Objective | Key tasks |
|---|---|---|---|
| 1–3 | Data collection | Establish ground truth for fire growth and weather | Pull daily FIRMS satellite detections for a set of historical fires to reconstruct footprint growth over time; pull matching GridMET weather data (wind, humidity, ERC/Burning Index) for the same locations and dates |
| 4–6 | First-pass spread model | Build and validate an initial predictive model | Train a Random Forest model that takes fire location and daily weather as input and predicts next-day spread distance and direction; validate against real historical growth; identify which fires the model handles poorly |
| 7–8 | Model improvement | Strengthen prediction accuracy | Compare against a second model type (XGBoost or a simple LSTM); incorporate fuel or vegetation moisture data if not already included |
| 9–10 | Population exposure | Translate spread predictions into human impact | Pull population density and Wildland-Urban Interface (WUI) distance data; calculate the number of people or structures newly exposed within each predicted spread radius |
| 11–12 | Ignition context | Add cause-based nuance | Pull gridded lightning strike data (NOAA NCEI); label historical fires as lightning- or human-caused using the FPA-FOD database; test whether ignition cause affects early spread behavior |
| 13–14 | Case study validation | Test the full pipeline against reality | Run the complete model on 2–3 real California fires and compare predicted spread and exposure to documented outcomes |
| 15 | Buffer | Absorb delays | Reserved for fixing whatever broke earlier in the timeline |
| 16–17 | Write-up and presentation | Prepare final deliverables | Assemble figures, board materials, and practice explaining methodology and limitations |
 
---
 
## Track 2: Real-time public signal and response gaps
 
**Research question:** Once a fire has started, does public information (news coverage, social media activity) reveal where official response or awareness may be lagging?
 
| Weeks | Phase | Objective | Key tasks |
|---|---|---|---|
| 1–3 | Data collection | Establish public-signal and fire ground truth | Pull GDELT (and optionally Reddit via PRAW) news/social volume and tone for the same historical fires used in Track 1; pull FIRMS spread data as the geographic ground truth |
| 4–5 | Human hotspot feature | Quantify human activity near fire-prone areas | Pull campground (Recreation.gov/USFS) and road/trail data (OpenStreetMap); build a percent-threshold proximity feature (e.g., percentage of ignitions within a set distance of a campground or road) |
| 6–8 | Response gap definition | Build the project's central, original metric | Compare social/news volume geographically against actual fire location day-by-day; test candidate definitions of a "quiet" area (mentions per capita, lag time before first local report) and select the most defensible one |
| 9–10 | First-pass validation | Test the metric against one case study | Apply the gap metric to a single historical fire; expect and plan for necessary adjustments |
| 11–12 | Metric refinement | Strengthen and diversify the signal | Adjust the gap definition based on Weeks 9–10 findings; incorporate a second data source (e.g., Reddit) if GDELT alone proves too sparse |
| 13–14 | Full validation | Test across all case studies | Check whether "quiet" areas correspond to documented evacuation delays or underreported damage across all selected fires |
| 15 | Visualization | Build the project's centerpiece figure | Construct a map or animation showing fire spread against social/news volume over time |
| 16 | Buffer | Absorb delays | Reserved for fixing whatever broke earlier in the timeline |
| 17 | Write-up and presentation | Prepare final deliverables | Assemble figures, board materials, and practice explaining methodology and limitations |
 
---
 
## Where the tracks converge
 
Both tracks are built around the same set of 2–3 historical case-study fires, which makes a combined closing narrative possible without extra dedicated project time:
 
> *Track 1's spread and exposure model shows where a fire is heading and who is affected in its path. Track 2's response-gap model, applied to the same fire, flags where public information about that same path was lagging.*
 
A natural checkpoint for syncing this combined view is **Weeks 13–14**, when both tracks are running full case-study validation in parallel.

"These people didn't get nitifed, and this is why"
finding a fialure or something to improve in for th enews sources... acitonable data if you can give a cause
what went wrong in alerting people about the fires - why did these people not evacuate even though they were informed.
basically just trying to figure out why these people died - then reccommending if we can do something
