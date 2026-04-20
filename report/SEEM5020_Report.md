# Frequency Estimation under the Strict Turnstile Model with α-Bounded Deletions

## 1. Introduction

This project studies frequency estimation in **strict turnstile streams** with the **α-bounded deletion property**. Each update has unit weight, prefixes remain nonnegative for every item, and the final stream volume satisfies

$$I + D \le \alpha F_1,$$

where `I` is the total number of insertions, `D` is the total number of deletions, and `F1` is the final `L1` mass of the stream.

The project required four algorithms:

- `Misra-Gries`
- `Space-Saving`
- `Count-Min Sketch`
- `Count-Sketch`

We implemented strict-turnstile extensions for the insertion-only methods and also implemented one advanced design candidate:

- `Integrated SpaceSaving±`

The final evaluation covers:

- parameter sweeps over `alpha` and stream length,
- multiple datasets,
- supplementary `epsilon` sweeps,
- and equal-logical-space comparisons.


## 2. Algorithms and Expected Behavior

The accompanying analysis document ([seem_5020_project.pdf](../seem_5020_project.pdf)) gives the theoretical intuition for each method.

### 2.1 Double-MG

`Double-MG` maintains two insertion-only Misra-Gries summaries: one for positive updates and one for negative updates. The analysis shows an additive error of order

\[
| \hat f_e - f_e | \le O(\alpha F_1 / k),
\]

so `O(alpha / epsilon)` counters are enough to target `epsilon F1` additive error.

### 2.2 Double-SS

`Double-SS` also keeps separate summaries for insertions and deletions, but uses Space-Saving instead of Misra-Gries. Its error can be written in a split form `I / m_I + D / m_D`, which again yields `O(alpha / epsilon)` space in the balanced case.

### 2.3 Integrated SpaceSaving±

`Integrated SpaceSaving±` uses a **single summary** that records insertion and deletion counts together. The theoretical appeal is that one summary can potentially achieve a better constant than two separate summaries. The analysis gives an additive error on the order of

\[
I / m \le \frac{\alpha + 1}{2m} F_1,
\]

which is again `O(alpha / epsilon)` space.

### 2.4 Count-Min Sketch

`Count-Min` already supports turnstile updates. Its standard point-query guarantee remains valid in strict turnstile streams:

\[
f_e \le \hat f_e \le f_e + \epsilon F_1
\]

with high probability, using `O((1/epsilon) log(1/delta))` space. The analysis also shows that the `alpha` property does **not** directly improve its main point-query bound.

### 2.5 Count-Sketch

`Count-Sketch` is also naturally turnstile-compatible. Its point-query error depends on `F2` or tail-`F2` rather than on the total `L1` churn. Therefore, `alpha` again does not directly improve its primary guarantee, but the method is expected to perform well as a turnstile baseline, especially when given a sufficiently large sketch.


## 3. Experimental Setup

### 3.1 Datasets

We used three datasets:

- **Uniform synthetic**
- **Zipf synthetic** with `s = 1.2`
- **Kosarak** click-stream data as the required real-world dataset

The project statement asked for a balanced synthetic dataset, a skewed synthetic dataset, and at least one real-world dataset. This requirement is satisfied by `uniform`, `zipf`, and `kosarak`.

### 3.2 Stream construction

All experiments used unit updates:

- `(item, +1)` for insertions
- `(item, -1)` for deletions

The final experiments use the **non-interleaved** deletion mode:

1. generate all insertions,
2. sample deletions from previously inserted occurrences,
3. append all deletions at the end.

This construction guarantees strict turnstile legality and matches the final project protocol used in the codebase.

### 3.3 Main parameter grid

The core experiment grid uses:

- `F1* in {5e4, 1e5, 2e5, 5e5}`
- `alpha in {1.5, 2, 3, 4, 6, 8}`

The original required values `{1.5, 2, 4, 8}` are included. We also added `3` and `6` to obtain smoother trends.

The actual stream length is measured as

\[
\text{stream length} = I + D.
\]

### 3.4 Metrics

We report:

- **Average normalized absolute error**
  - `avg |f_hat - f| / F1`
- **Average relative error**
  - `avg |f_hat - f| / max(f, 1)`
- **Heavy-hitter F1**
  - overlap between true and estimated top-`k` items
- **Logical size**
  - the number of counters or cells used by the data structure
- **Memory usage in bytes**

### 3.5 Supplementary experiments

To better understand the trade-offs, we also ran:

- an **epsilon sweep** with `epsilon in {0.01, 0.05, 0.1}`,
- an **equal-logical-space comparison** with budgets `L in {300, 600, 1200, 2400}`.


## 4. Main Results

### 4.1 Baseline comparison

The baseline uses the default parameterization in the implementation, especially `epsilon = 0.01` for the sketch-based methods.

Average performance across the full baseline grid is summarized below.

| Algorithm | Avg. normalized abs. error | Avg. relative error | Avg. HH-F1 | Avg. logical size |
| --- | ---: | ---: | ---: | ---: |
| Count-Sketch | `8.0e-06` | `0.94` | `0.689` | `50000` |
| Double-MG | `3.6e-05` | `1.00` | `0.422` | `815` |
| Integrated SpaceSaving± | `9.5e-05` | `3.13` | `0.123` | `254` |
| Count-Min | `2.0e-03` | `213.66` | `0.448` | `1360` |
| Double-SS | `2.46e-03` | `274.99` | `0.422` | `817` |

The main conclusion is straightforward:

- **Count-Sketch gives the best point-query accuracy in the baseline setting.**
- **Double-MG is the best summary-based method.**
- **Integrated SpaceSaving± is clearly more space-efficient than Double-MG, but it does not beat Double-MG in accuracy.**
- **Count-Min and Double-SS are much worse on point-query error, especially on relative error.**

This ranking is consistent with the implementation choices. `Count-Sketch` is a turnstile-native method and, under the default `epsilon = 0.01`, it uses a very large sketch (`logical_size = 50000`). The summary-based methods use far fewer counters, so the baseline is not a fair equal-space comparison.


### 4.2 Effect of `alpha`

The main alpha plots are shown in:

- ![Alpha sweep, normalized error](figures/project_required_expanded/alpha_triptych_error_space.png)
- ![Alpha sweep, relative error](figures/project_required_expanded/alpha_triptych_relative_error_space.png)

The most important patterns are:

- `Count-Sketch` and `Count-Min` are **almost flat** as `alpha` changes.
  - This is expected because their baseline sizes are determined mainly by `epsilon` and `delta`, not by `alpha`.
- `Double-MG` improves slightly as `alpha` increases.
  - In our implementation, its capacity scales with `alpha`, so the method is given more counters when churn is larger.
- `Double-SS` also improves with larger `alpha`, but remains much less accurate than `Double-MG`.
- `Integrated SpaceSaving±` behaves differently: its error **increases** with `alpha` even though its capacity also increases.

This last point is important. The theory suggests that an integrated summary could exploit bounded deletions efficiently, but the current one-summary implementation is sensitive to heavy churn. In practice, larger `alpha` creates more opportunities for stale entries and missed deletions, and the current design does not compensate well for that effect.


### 4.3 Effect of stream length

The main stream-length plots are shown in:

- ![Stream-length sweep, normalized error](figures/project_required_expanded/stream_length_triptych_error_space_alpha_4p0.png)
- ![Stream-length sweep, relative error](figures/project_required_expanded/stream_length_triptych_relative_error_space_alpha_4p0.png)

Stream length increases through the `F1*` grid. We observe:

- `Count-Sketch` remains very stable.
- `Count-Min` remains poor and does not improve meaningfully with longer streams.
- `Double-MG` improves as the stream becomes longer.
- `Integrated SpaceSaving±` also improves as `F1*` increases, but it remains consistently behind `Double-MG`.

This behavior is reasonable. When the final mass grows, repeated heavy items become easier for summary-based methods to stabilize, while the sketch-based methods already operate in a regime where the default sketch is large enough that their error is nearly saturated.


### 4.4 Dataset diversity

The three datasets exhibit clearly different behavior.

#### Uniform

- No clear heavy hitters exist.
- Heavy-hitter F1 is low for almost all methods.
- `Double-MG` gives the best normalized absolute error.

This is reasonable: in a nearly flat distribution, a summary method that aggressively suppresses weak items can still achieve small normalized point-query error, while heavy-hitter recovery itself becomes ill-defined.

#### Zipf

- `Count-Sketch` is best.
- `Double-MG` is the best summary-based method.
- `Count-Min` achieves fairly strong heavy-hitter recovery, but its point-query error is still much larger than that of `Count-Sketch` and `Double-MG`.

This matches the intuition that skew helps heavy-hitter identification, especially for methods that preserve large counts.

#### Kosarak

- The pattern is similar to Zipf.
- `Count-Sketch` is nearly perfect on heavy hitters (`HH-F1` close to `0.99`).
- `Double-MG` is again the best summary-based method.

Kosarak is a realistic click-stream dataset with clear popularity skew, so these outcomes are consistent with the expected strengths of Count-Sketch and MG-style summaries.


## 5. Epsilon Sweep

The supplementary epsilon plots are:

- ![Epsilon sweep, normalized error](figures/project_required_expanded/epsilon_triptych_error_space_alpha_4p0_f1_100000.png)
- ![Epsilon sweep, relative error](figures/project_required_expanded/epsilon_triptych_relative_error_space_alpha_4p0_f1_100000.png)

At fixed `alpha = 4` and `F1* = 100000`, all methods degrade as `epsilon` increases and their space decreases.

Representative averages across the three datasets are:

| Algorithm | `epsilon=0.01` | `epsilon=0.05` | `epsilon=0.10` |
| --- | ---: | ---: | ---: |
| Double-MG | `3.9e-05` | `4.8e-05` | `5.2e-05` |
| Integrated SpaceSaving± | `1.04e-04` | `1.34e-04` | `1.45e-04` |
| Count-Sketch | `8.0e-06` | `1.59e-04` | `7.19e-04` |
| Count-Min | `2.03e-03` | `1.18e-02` | `2.48e-02` |
| Double-SS | `1.72e-03` | `1.00e-02` | `2.13e-02` |

Two observations matter:

- `Count-Sketch` is excellent at `epsilon=0.01`, but it loses much of its advantage once its sketch is reduced aggressively.
- `Double-MG` and `Integrated SpaceSaving±` degrade more smoothly under reduced space.

This is exactly why the equal-space study is important: the baseline `Count-Sketch` advantage is partly a consequence of a much larger sketch.


## 6. Equal Logical Space Comparison

The equal-space plots are:

- ![Equal-space error vs budget](figures/project_required_expanded/equal_space_triptych_error_alpha_4p0_f1_100000.png)
- ![Equal-space relative error vs budget](figures/project_required_expanded/equal_space_triptych_relative_error_alpha_4p0_f1_100000.png)
- ![Equal-space alpha sweep](figures/project_required_expanded/equal_space_alpha_triptych_L_1200_f1_100000.png)
- ![Equal-space alpha sweep, relative error](figures/project_required_expanded/equal_space_alpha_triptych_relative_error_L_1200_f1_100000.png)
- ![Equal-space stream-length sweep](figures/project_required_expanded/equal_space_stream_triptych_L_1200_alpha_4p0.png)
- ![Equal-space stream-length sweep, relative error](figures/project_required_expanded/equal_space_stream_triptych_relative_error_L_1200_alpha_4p0.png)

This experiment is the fairest way to compare the algorithms. Once we force all methods to use the same logical budget, the ranking changes substantially.

At `alpha = 4` and `F1* = 100000`, averaged across datasets:

### Budget `L = 1200`

| Algorithm | Avg. normalized abs. error | Avg. relative error | Avg. HH-F1 |
| --- | ---: | ---: | ---: |
| Double-MG | `3.6e-05` | `0.99` | `0.550` |
| Integrated SpaceSaving± | `6.6e-05` | `2.86` | `0.510` |
| Count-Sketch | `3.79e-04` | `26.25` | `0.233` |
| Double-SS | `1.09e-03` | `79.38` | `0.553` |
| Count-Min | `2.25e-03` | `162.08` | `0.413` |

### Budget `L = 2400`

| Algorithm | Avg. normalized abs. error | Avg. relative error | Avg. HH-F1 |
| --- | ---: | ---: | ---: |
| Double-MG | `3.2e-05` | `0.99` | `0.660` |
| Integrated SpaceSaving± | `4.7e-05` | `2.59` | `0.667` |
| Count-Sketch | `1.49e-04` | `10.15` | `0.470` |
| Double-SS | `5.01e-04` | `37.05` | `0.660` |
| Count-Min | `9.94e-04` | `72.19` | `0.570` |

These equal-space results are crucial:

- `Count-Sketch` is **no longer dominant** once it is forced to use the same space budget as the summary methods.
- `Double-MG` becomes the strongest point-query method.
- `Integrated SpaceSaving±` becomes the second-best point-query method and narrows the gap as the budget grows.
- At the largest tested budget, `Integrated SpaceSaving±` slightly exceeds `Double-MG` on heavy-hitter F1, even though its point-query error is still larger.

So the supplementary experiments strongly support the conclusion that the baseline `Count-Sketch` win was driven by both algorithmic strength **and** a much larger sketch size.


## 7. Method-by-Method Discussion

### Double-MG

**Strengths**

- Best summary-based point-query accuracy.
- Very stable across datasets.
- Strong equal-space performance.
- Simple and robust.

**Weaknesses**

- Relative error stays near `1` because many low-frequency items are estimated as zero.
- Heavy-hitter recovery is weaker than Count-Sketch on strongly skewed data.

### Double-SS

**Strengths**

- Competitive heavy-hitter F1 at larger budgets.
- Improves when more space is allocated.

**Weaknesses**

- Much larger point-query error than Double-MG.
- Very large relative error.
- Bias from two separate overestimating summaries is not canceled by subtraction.

### Count-Min Sketch

**Strengths**

- Good heavy-hitter recovery on skewed datasets.
- Well-understood guarantee under strict turnstile.

**Weaknesses**

- Very poor relative error.
- Point-query performance is much worse than Count-Sketch and Double-MG.
- Collision-induced overestimation hurts low-frequency items severely.

### Count-Sketch

**Strengths**

- Best baseline point-query accuracy.
- Best heavy-hitter F1 on skewed and real data.
- Naturally supports turnstile updates.

**Weaknesses**

- Uses by far the largest sketch in the baseline setting.
- Loses its dominant advantage in equal-space comparisons.

### Integrated SpaceSaving±

**Strengths**

- Small logical size.
- Much better point-query performance than Count-Min and Double-SS.
- Competitive in equal-space heavy-hitter recovery at larger budgets.

**Weaknesses**

- Worse than Double-MG in all point-query experiments.
- Heavy-hitter recovery is relatively weak in the current implementation.
- Becomes less robust as `alpha` increases.


## 8. Why Does Double-MG Still Beat Integrated SpaceSaving±?

This is the most important qualitative finding of the project.

The theory suggests that an integrated summary can achieve an attractive constant in the `O(alpha / epsilon)` regime. However, in our experiments `Double-MG` still outperforms `Integrated SpaceSaving±`. The result is reasonable for three concrete reasons.

### 8.1 The final stream schedule favors Double-MG

The final experiments use the **non-interleaved** schedule, where all insertions appear first and all deletions appear later. `Double-MG` decomposes the stream into exactly the two insertion-only problems that MG handles best:

- one summary for insertions,
- one summary for deletions.

This makes the data flow particularly natural for `Double-MG`.

### 8.2 Under the default `epsilon` rule, Double-MG is given more space

In the baseline setting, `Double-MG` receives more logical counters than `Integrated SpaceSaving±` for the same nominal `epsilon` parameter. Therefore, part of the baseline gap is simply a space-allocation effect.

However, the equal-space experiments show that this is **not** the whole story, because `Double-MG` still remains slightly better even when budgets are matched.

### 8.3 The implemented integrated summary is a simplified one-summary design

The current implementation is a simplified `Integrated SpaceSaving±` variant. In particular:

- deletions of unmonitored items are ignored when the summary is full,
- replacement is driven by minimum insertion count,
- high churn can leave stale entries inside the summary.

These design choices are reasonable for a first implementation, but they make the method less robust under large deletion pressure. This explains why the method does not realize its theoretical promise in the current codebase.

So the correct conclusion is **not** that the integrated idea is wrong. Instead, the conclusion is that the current one-summary implementation is still weaker than `Double-MG` in practice, especially for point queries.


## 9. Advanced Solution Design

The advanced design required by the project is not only to implement one candidate, but also to propose an improved idea.

Based on the theory and the experiments, a promising next step is a **hybrid integrated summary + residual sketch**:

1. Keep a single integrated summary for monitored heavy items.
2. Track ignored deletions and evicted residual mass in a small residual sketch.
3. Use a better admission / eviction rule based on estimated net frequency rather than insertion count alone.
4. Answer each query by combining the summary estimate with the residual sketch estimate.

This design targets the main weaknesses observed in the current integrated method:

- stale entries under churn,
- ignored deletions,
- poor low-frequency handling.

Conceptually, such a hybrid could preserve the low summary cost of `Integrated SpaceSaving±` while reducing the gap to `Double-MG` and `Count-Sketch`.


## 10. Conclusion

The project leads to four main conclusions.

1. **Count-Sketch is the strongest baseline point-query method**, but much of its advantage comes from using a very large sketch.
2. **Double-MG is the best summary-based method** and remains the strongest point-query method under equal logical space.
3. **Integrated SpaceSaving± is promising but not yet superior**. It is compact and becomes competitive under matched budgets, but it does not beat Double-MG in the current implementation.
4. **Equal-space evaluation is essential**. Without it, the baseline results overstate the practical advantage of Count-Sketch.

Overall, the experiments are consistent with the theory in the analysis PDF:

- bounded-deletion-aware summaries are meaningful and competitive,
- turnstile-native sketches remain strong baselines,
- and advanced one-summary designs are attractive, but their real performance depends heavily on the details of update handling and admission policy.
