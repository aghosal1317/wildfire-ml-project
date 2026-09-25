## Diagnosing and Simulating Alert Failures in U.S. Wildfire Evacuations

## Motivating Question / Problem Statement

Lahaina's Attorney General investigation found officals received an advanced warning days before the fire, yet 102 people died. The county's siren system was never activated, and communication failed because cell service went down. The danger was known, so this wasn't exactly a prediction failure, it was a failure to warn people who needed to take action immideiately. There is a good amount of wildfire models that predict where the fire will go, but not as much work for why warnings fail to reach people. Regardless, failure to alert people in danger is the recurring reason for death tolls during wildfires.

## Background / Related Work

Lever and Acrucci's Sentimental Wildfires (2022) uses Twitter data and satellite fire data to nowcast severity in real time. They called social media a human sensor network. It was made for already active and burning fires, not diagnosing why official warnings fail to reach people. My project builds on the human-sensor concept but uses it to compare when public awareness emerged against when official alerts came out.

Hawaii Attorney General investigation in the 2023 Lahaina fire was the most prominent and dangerous alert failure. Sirens weren't activated, power outages, no commands to evacuate. Like mentioned in the problem statement, they had many days to notify the public, but failed to. This investigation covers one case, and doesn't test what changes could be made for a better outcome. My project builds on this one by combining it with other fire failure analysis and adds a problem counter that this report does not have.

For simulations, WUI-NITY couples FARSITE fire spread data with traffic modeling. Pishahang et al. (2025) built a Bayesian model of 2018 camp fire evacuation data. He tested it against different scenarios and validated it by firefighters who were in the area. Both show that the kind of simulation I am proposing is plausible, but look at how fast people are moving rather than the alert chain. My project tries to build on their ideas of a simulation, but in a different way. It may also be interesting to implement something similar into my project: once notifications do reach people, how do they evacuate, and if they don't, why not?

CBS News did an investigation and found at least a dozen US disasters with alert failures in the past decade. It showed Lahaina has a pattern of under-alerting citizens, which shows me this problem was not just a one time thing.

## Research Question / Hypothesis

Across multiple documented U.S. wildfire disasters, what specifically in the alert for evacuation process contributed most to deaths, and how much would specific interventions have reduced casualties (measured by a simulation calibrated to real documented timelines)?


## Proposed Approach / Methodology /Data

Failure analysis (from Hawaii AG report): 
- Build a minute by minute timeline for each case study after ignition
- - Find first warning issued and by what channel
- - Evacuation alerts issued
- - Fire arrival
- - Casualties

Simulation: population agent with features like mobility, distance to exit, alert-channel access on a grid representing the affected community. Would have a fire spread model (possibily Tarun's, but using FARSITE data) and an "alert" module. Calibrate the model using the Lahaina timeline, then vary parameters like alert delay and siren failures to record changes in simulated deaths. 

## Milestones / Variations

1. Build failure timeline + taxonomy for Case 1 (Lahaina)
2. Build baseline simulation environment (agents, grid, alert modules)
3. Calibrate/validate baseline simulation against Lahaina's real documented outcome, tweak based on accuracy
4. Run counter interventions on Case 1, record effects

Additional analysis / variation:

5. Repeat timeline + simulation for Case 2 (Camp Fire)
6. Synthesize taxonomy + simulation results into final recommendations 

## Expected Outcomes / Significance

Success would be an estimate with a quantitiy (for example, earlier alerts reduced deaths by X%). Additionally, I would want a taxonomy that uses multiple failures from different cases, with recommendations for how to treat the documented failures. The significance of this project is to make a generalizable recommendation framework that could inform emergency responders and news sources about how to improve rather than just describing their faults.

## Risks / Open Questions

Calibration will be done using public, limited data. Additionally, the simulation cannot "predict" real world outcomes because it is after the fact, so results need to be framed as "our simulation shows this could've happened in the past" not in the future. Since the project contains death, I will have to be careful with tone and framing.

## References

Lever, J., & Arcucci, R. (2022). Sentimental wildfire: a social-physics machine learning model for wildfire nowcasting. Journal of Computational Social Science, 5(2), 1427–1465. https://doi.org/10.1007/s42001-022-00174-8

Hawaii Department of the Attorney General. (2024). Maui Wildfires: Comprehensive Timeline Report (Phase One report on the 2023 Lahaina fire). Department of the Attorney General, State of Hawaii. https://www.cnn.com/2024/09/14/us/hawaii-maui-wildfire-report/index.html

Wahlqvist, J., Ronchi, E., Gwynne, S. M. V., et al. (2021). The simulation of wildland-urban interface fire evacuation: The WUI-NITY platform. Safety Science, 136, 105145. https://doi.org/10.1016/j.ssci.2020.105145

Pishahang, M., Ruiz-Tagle, A., Ramos, M. A., Droguett, E. L., & Mosleh, A. (2024). A Bayesian agent-based model and software for wildfire safe evacuation planning and management. Proceedings of the Institution of Mechanical Engineers, Part O: Journal of Risk and Reliability. https://doi.org/10.1177/1748006X241259215

CBS News. (n.d.). Investigation into U.S. disasters where officials failed to issue timely emergency alerts. https://www.cbsnews.com

https://dl.acm.org/doi/epdf/10.1145/3137597.3137602 