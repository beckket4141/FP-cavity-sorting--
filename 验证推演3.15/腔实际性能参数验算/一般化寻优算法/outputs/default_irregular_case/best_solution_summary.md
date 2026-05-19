# Best Solution Summary

- Case: `default_irregular_case`
- Best region: `R015`
- Representative k: `0.280720000`
- Representative L/R: `0.595911572`
- Candidate set size: `12`
- Candidate modes: `[1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]`
- Best coexistence subset size: `8`
- Best coexistence subset: `[1,10,18,22,27,31,37,46]`
- s_min: `0.104880000`
- F_min: `28.604119`
- F_eval used: `32.000000`
- Average ER_sum: `12.714077 dB`
- Minimum ER_sum: `12.012139 dB`
- Average separation efficiency: `94.8811%`
- Minimum separation efficiency: `94.0805%`

Why this one ranks first:

- It has the highest-ranked subset size under the configured feasibility budget.
- Within that cardinality, it offers the largest s_min / lowest F_min according to the configured sort priorities.
- It also respects the configured geometry preference through the L/R distance term in the ranking.
