# 1. https://link.springer.com/article/10.1007/s42001-022-00174-8 
- This paper builds a machine learning model that reads Twitter sentiment (the negativity and frequency of people’s posts) and pairs it with satellite fire data to predict wildfire severity in real time.
- They found lower sentiment (more emotional posts) in a region that correlates how severe people perceive a disaster to be. This shows that the public mood can actually become a “sensor” for fire impact .
# 2. https://nhess.copernicus.org/articles/25/4713/2025/
- Uses Random Forest models to predict where human-caused fires are likely to start, based on distance to cities, roads, and farmland edges across several European regions.
- Instead of using one big model for Europe, they have built multiple small localized models per region and compared them
What matters in one area does not matter in another
# 3. https://link.springer.com/article/10.1007/s11069-023-06172-x
- Trains an ensemble ML model on a huge feature set (76 variables, such as terrain, land cover, human activity, climate) to predict day-by-day ignition probability across a large chunk of Northern California.
- According to the authors, “Feature importance analysis shows that the Topographic Wetness Index is the most important climatic predictor, while population density and land cover development are also highly rated.”
- They kind of take on the “needle in a haystack” problem. Actual fire start days are considerably rarer compared to fire free days, so they test different ways to predict and sort of correct this imbalance so the model doesn’t always predict “no fire”.

# 4. https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024EF005744

- This study looks at whether the 2020 wildfire season had an unusually high number of human caused ignitions, and claims the reason for this is the increased number of people participating in outdoor recreation activities during COVID lockdowns.
- Instead of using just the weather, they also used campground reservation numbers and closures to see how many people were actually in the woods. They also used fireworks sales to see if that risky human behavior explains the spike.
# 5. https://doi.org/10.1071/WF21177
- The researchers map where, statistically, fires cluster geographically
- - They then split it by cause, either lightning started or human started
- Human fires spike in spring near towns and campsites, lightning fires spike in summer during storms
- - I think they should be two different models instead of lumping all types of ignitions together
