# Driving Test Centre Analysis

Overview: This project analyzes data from two driving test centers (Mill Hill and Wood Green) to help an individual choose the optimal test center based on passing rate probabilities. The analysis considers the influence of factors like age, gender, location, and year on the probability of passing the driving test.

Objective: Provide a data-driven recommendation for the most suitable driving test center by comparing passing rates at each location, accounting for the individual’s characteristics.

Key Components: 
  1. Data Collection: Compiled driving test data (2007–2023) from the UK government, focusing on Mill Hill and Wood Green test centers, and created a structured dataset for analysis.
  2. Logistic Regression Analysis:
     - Used logistic regression to model the probability of passing based on the factors (location, age, gender, and year).
     - Achieved insights into the influence of each factor, revealing slightly higher predicted pass rates at Mill Hill.
     - Evaluated model performance through accuracy, ROC curve, and AUC scores, with moderate prediction accuracy.
  3. Wald Test for Equality of Means:
     - Conducted a Wald test to check if passing rates significantly differ between Mill Hill and Wood Green.
     - Resulted in no significant difference, suggesting either location could be chosen based on this test.

Key Technologies:
  - R (data cleaning, logistic regression, and statistical testing)
  - ggplot2 for visualizations
  - Statistical methods: Logistic regression, Wald test

Outcome: Based on logistic regression, Mill Hill had a marginally higher predicted passing rate. However, the Wald test indicated no significant difference between the two locations, suggesting either center as a viable option. The analysis demonstrates both the potential and limitations of statistical methods in guiding practical decision-making.
