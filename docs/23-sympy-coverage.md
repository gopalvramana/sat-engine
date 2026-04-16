# SymPy Pipeline — Coverage Reference

Last updated: 2026-04-16  
Source of truth: `sat-engine/scripts/math_engine.py`

**Coverage: 28 topics (96%) · 22 diagram types (88%)**

---

## Question Types & Difficulty Levels by Topic

All 28 topics implement **D1–D5** fully. D6–D7 are not implemented (fall back to D4 in the CLI).

| Topic | Code | Domain | D1 | D2 | D3 | D4 | D5 | SPR Difficulties |
|---|---|---|---|---|---|---|---|---|
| Linear equations (1 variable) | LEQ | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D3 (30%), D4 (40%) |
| Linear equation word problems | LWP | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Systems of linear equations | SLE | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Linear functions | LFN | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Quadratic equations | QEQ | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D4 (40%) |
| Linear inequalities | LNI | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Absolute value | ABV | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Percentages | PCT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Ratios & rates | RAT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Proportional relationships | PRP | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Statistics | STA | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Probability | PRB | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Two-way tables | TWT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Scatterplot analysis | SCA | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Data analysis | DAT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Pythagorean theorem | PYT | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | D3 (40%), D4 (40%) |
| Area (2D shapes) | ARA | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | D4 (40%) |
| Coordinate geometry | CGE | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Circles | CIR | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Volume (3D shapes) | VOL | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Plane geometry | PLG | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Special triangles | SPT | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Trigonometry | TRG | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Exponents & radicals | EXR | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Polynomial operations | POL | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Quadratic functions | QFN | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Sequences & series | SEQ | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Complex numbers | CMX | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |

**SPR** = Student-Produced Response (numeric grid-in). All other difficulties are MCQ (4 choices).  
Topics with no SPR column produce MCQ only at all difficulties.

---

## Difficulty Progression by Topic

### Linear Equations — One Variable (LEQ)
| D | Question Type | What Changes |
|---|---|---|
| D1 | ax + b = c | Small integers (a,b,c ≤ 9), integer answer |
| D2 | ax + b = c | Larger coefficients (up to 15) |
| D3 | ax + b = c | Negatives allowed; 30% SPR |
| D4 | ax + b = c | Fractional answers possible; 40% SPR |
| D5 | ax + b = cx + d | Variables on both sides |

### Linear Equation Word Problems (LWP)
| D | Problem Type |
|---|---|
| D1 | Rate × quantity + fixed fee (e.g. phone bill) |
| D2 | Rate × quantity + fixed fee (wider range) |
| D3 | Two unknowns summing to total with given difference |
| D4 | Two different unit rates, total cost (mixture-style) |
| D5 | Two objects traveling at different speeds (d = st) |

### Systems of Linear Equations (SLE)
| D | Form |
|---|---|
| D1 | x + y = S, x − y = D (simple elimination) |
| D2 | ax + y = c₁, x + by = c₂ |
| D3 | General a₁x + b₁y = c₁, a₂x + b₂y = c₂ with negatives |
| D4 | Larger coefficients (2–6) |
| D5 | Largest coefficients (3–8), wider answer range |

### Linear Functions (LFN)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Evaluate f(x) at given x | Coordinate plane + point |
| D2 | Find slope of y = mx + b | Coordinate plane (equation hidden) |
| D3 | Find x-intercept (where y = 0) | Coordinate plane + x-intercept |
| D4 | Find y-intercept from two points | Coordinate plane + 2 points |
| D5 | Y-intercept of parallel line through a given point | Coordinate plane + point |

### Quadratic Equations (QEQ)
| D | Form | What is Asked |
|---|---|---|
| D1 | (x − r)² = 0 | Single root (perfect square) |
| D2 | x² + bx + c = 0 | Two positive integer roots |
| D3 | x² + bx + c = 0 | One positive, one negative root |
| D4 | ax² + bx + c = 0 (a > 1) | Positive root; 40% SPR |
| D5 | x² + bx + c = 0 | Product of roots (= c) |

### Linear Inequalities (LNI)
| D | Problem Type | Diagram |
|---|---|---|
| D1 | ax + b > c (simple, positive solution) | number_line |
| D2 | ax + b ≤ c (integer boundary) | number_line |
| D3 | ax + b > cx + d (variables on both sides) | number_line |
| D4 | Compound inequality a < bx + c < d | number_line |
| D5 | Word problem → inequality → solve | number_line |

### Absolute Value (ABV)
| D | Problem Type |
|---|---|
| D1 | \|x\| = a (single solution) |
| D2 | \|ax + b\| = c (two solutions) |
| D3 | \|ax + b\| < c (compound inequality) |
| D4 | \|ax + b\| > c (disjoint inequality) |
| D5 | Word problem with absolute value constraint |

### Percentages (PCT)
| D | Problem Type |
|---|---|
| D1 | Find p% of n (clean percentages) |
| D2 | Find what percent part is of whole |
| D3 | Percent change (increase or decrease) |
| D4 | Find original value given final and percent increase |
| D5 | Compound percent changes (two sequential %) |

### Ratios & Rates (RAT)
| D | Problem Type |
|---|---|
| D1 | Divide total in ratio a:b |
| D2 | Unit rate (n items → m items cost) |
| D3 | Divide total in 3-part ratio a:b:c |
| D4 | Distance / speed / time (find t) |
| D5 | Average speed (two legs at different speeds) |

### Proportional Relationships (PRP)
| D | Problem Type |
|---|---|
| D1 | Given k and x, find y = kx |
| D2 | Given (x₁,y₁) and x₂, find y₂ |
| D3 | Fractional constant y = (a/b)x |
| D4 | Reverse: given k and y, find x |
| D5 | Table with missing value (4 data points) |

### Statistics (STA)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Mean of a data set | — |
| D2 | Median of a data set | — |
| D3 | Mode and range | — |
| D4 | IQR (Q3 − Q1) | box_plot |
| D5 | Standard deviation (conceptual) | — |

### Probability (PRB)
| D | Problem Type |
|---|---|
| D1 | Simple probability P(A) = favorable/total |
| D2 | Complement probability P(not A) = 1 − P(A) |
| D3 | Two independent events P(A and B) |
| D4 | Conditional probability P(A\|B) |
| D5 | At-least-one probability using complement |

### Two-Way Tables (TWT)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Joint frequency (read a single cell) | two_way_table |
| D2 | Marginal frequency (row/column total) | two_way_table |
| D3 | Conditional frequency (given row or column) | two_way_table |
| D4 | Missing cell (total − known cells) | two_way_table |
| D5 | Conditional probability from table | two_way_table |

### Scatterplot Analysis (SCA)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Read a value from the scatter plot | scatter_plot |
| D2 | Identify positive/negative association | scatter_plot |
| D3 | Use line of best fit to predict a value | scatter_plot |
| D4 | Interpret slope of line of best fit | scatter_plot |
| D5 | Identify outlier or residual | scatter_plot |

### Data Analysis (DAT)
| D | Chart Type | What is Asked |
|---|---|---|
| D1 | Bar chart | Read a specific bar value |
| D2 | Bar chart | Max − min difference |
| D3 | Pie chart | Convert % to count (count = total × pct / 100) |
| D4 | Bar chart (missing bar) | Find missing value (missing = total − known) |
| D5 | Bar chart | Calculate one category as % of total |

### Pythagorean Theorem (PYT)
| D | Form | Diagram |
|---|---|---|
| D1 | Find hypotenuse (simple triple) | right_triangle (hyp = ?) |
| D2 | Find leg (simple triple) | right_triangle (leg = ?) |
| D3 | Find hypotenuse (scaled triple); 40% SPR | right_triangle (hyp = ?) |
| D4 | Find hypotenuse (scaled triple); 40% SPR | right_triangle (hyp = ?) |
| D5 | Find area of triangle (leg + hypotenuse given) | right_triangle (leg = ?) |

### Area 2D (ARA)
| D | Shape | Diagram |
|---|---|---|
| D1 | Rectangle A = l × w | rectangle |
| D2 | Triangle A = ½bh | triangle |
| D3 | Composite L-shaped area | composite_rectangle |
| D4 | Rectangle — find missing width; 40% SPR | rectangle (w = ?) |
| D5 | Scaling — if dimensions scale by k, area scales by k² | scaled_rectangle |

### Coordinate Geometry (CGE)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Slope between two points | Coordinate plane + 2 points |
| D2 | X-coordinate of midpoint | Coordinate plane + midpoint |
| D3 | Distance between two points | Coordinate plane + 2 points |
| D4 | Missing endpoint given midpoint and one endpoint | Coordinate plane + highlight |
| D5 | Y-coordinate of third collinear point | Coordinate plane + 3 points + line |

### Circles (CIR)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Circumference given radius (C = 2πr) | circle (radius) |
| D2 | Area given radius (A = πr²) | circle (radius) |
| D3 | Circumference given diameter (C = πd) | circle (diameter) |
| D4 | Arc length of sector — answer as Nπ | circle + sector (angle θ) |
| D5 | Sector area — answer as Nπ | circle + sector (angle θ) |

### Volume 3D (VOL)
| D | Shape | Formula | Diagram |
|---|---|---|---|
| D1 | Rectangular prism | V = l·w·h | rectangular_prism |
| D2 | Cylinder | V = πr²h | cylinder |
| D3 | Cone | V = ⅓πr²h | cone |
| D4 | Sphere | V = 4/3 πr³ | sphere |
| D5 | Cylinder (find height) | V = πr²h → h = V/πr² | cylinder (h = ?) |

### Plane Geometry (PLG)
| D | Shape | What is Asked | Diagram |
|---|---|---|---|
| D1 | Parallelogram | Area = base × height | parallelogram |
| D2 | Trapezoid | Area = ½(b₁+b₂)h | trapezoid |
| D3 | Parallelogram | Find missing height | parallelogram (h = ?) |
| D4 | Trapezoid | Find missing height | trapezoid (h = ?) |
| D5 | House shape (rect + triangle) | Total composite area | house_shape |

### Special Triangles (SPT)
| D | Type | What is Asked | Diagram |
|---|---|---|---|
| D1 | 45-45-90 | Find hypotenuse given leg | special_triangle |
| D2 | 30-60-90 | Find long leg given short leg | special_triangle |
| D3 | 45-45-90 | Find leg given hypotenuse | special_triangle |
| D4 | 30-60-90 | Find hypotenuse given long leg | special_triangle |
| D5 | Mixed | Multi-step using triangle ratios | special_triangle |

### Trigonometry (TRG)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | sin θ = opposite/hypotenuse | right_triangle (label_angle) |
| D2 | cos θ = adjacent/hypotenuse | right_triangle (label_angle) |
| D3 | tan θ = opposite/adjacent | right_triangle (label_angle) |
| D4 | Find missing side using SOHCAHTOA | right_triangle (label_angle) |
| D5 | Find angle given ratio (inverse trig conceptual) | right_triangle (label_angle) |

### Exponents & Radicals (EXR)
| D | Rule | What is Asked |
|---|---|---|
| D1 | Product rule: xᵃ · xᵇ = xᵃ⁺ᵇ | Simplify expression |
| D2 | Power of a power: (xᵃ)ᵇ = xᵃᵇ | Simplify expression |
| D3 | Simplify √(a·b²) | Extract perfect square factors |
| D4 | Rational exponents: x^(1/n) = ⁿ√x | Convert and evaluate |
| D5 | Negative exponents: x⁻ⁿ = 1/xⁿ | Simplify expression |

### Polynomial Operations (POL)
| D | Operation | What is Asked |
|---|---|---|
| D1 | FOIL: (x + a)(x + b) | Expand to standard form |
| D2 | Factor: x² + bx + c | Find factors |
| D3 | Evaluate: p(a) for given a | Substitute and compute |
| D4 | Add/subtract polynomials | Combine like terms |
| D5 | Divide: (x² + bx + c) ÷ (x + a) | Polynomial long division |

### Quadratic Functions (QFN)
| D | Form | What is Asked | Diagram |
|---|---|---|---|
| D1 | f(x) = (x − h)² + k | Identify vertex | parabola |
| D2 | f(x) = a(x − h)² + k | Min/max value | parabola |
| D3 | f(x) = (x − h)² + k | Minimum value of function | parabola |
| D4 | f(x) = ax² + bx + c | Axis of symmetry x = −b/2a | parabola |
| D5 | f(x) = a(x − h)² + k | Interpret transformation | parabola |

### Sequences & Series (SEQ)
| D | Type | What is Asked |
|---|---|---|
| D1 | Arithmetic: nth term = a + (n−1)d | Find nth term |
| D2 | Geometric: nth term = a · rⁿ⁻¹ | Find nth term |
| D3 | Arithmetic series | Sum of first n terms |
| D4 | Geometric series | Sum of finite geometric series |
| D5 | Mixed | Identify sequence type and find term |

### Complex Numbers (CMX)
| D | Operation | What is Asked |
|---|---|---|
| D1 | Add/subtract complex numbers | Combine real and imaginary parts |
| D2 | Multiply: (a + bi)(c + di) | Expand using i² = −1 |
| D3 | Powers of i (i¹ through i⁴ cycle) | Evaluate iⁿ |
| D4 | Modulus: \|a + bi\| = √(a² + b²) | Find absolute value |
| D5 | Divide: (a + bi)/(c + di) | Multiply by conjugate |

---

## Diagram Types

| Diagram Type | Topics | Notes |
|---|---|---|
| `coordinate_plane` | LFN (D1–D5), CGE (D1–D5) | Function line, data points, highlight_point, hideLabel flag |
| `right_triangle` | PYT (D1–D5), TRG (D1–D5) | Legs and hypotenuse; missing value shown as "?"; label_angle for trig |
| `special_triangle` | SPT (D1–D5) | 30-60-90 or 45-45-90 with angle arcs and labeled sides |
| `rectangle` | ARA (D1, D4) | Length × width; D4 has width = "?" |
| `triangle` | ARA (D2) | Base and height with dashed altitude |
| `composite_rectangle` | ARA (D3) | L-shaped figure with labeled sub-dimensions |
| `scaled_rectangle` | ARA (D5) | Two rectangles with scale arrow (× k) |
| `circle` | CIR (D1–D5) | D1–D3: radius or diameter; D4–D5: sector with angle θ |
| `parallelogram` | PLG (D1, D3) | Height shown as dashed vertical line inside shape |
| `trapezoid` | PLG (D2, D4) | Both parallel sides and dashed height labeled |
| `house_shape` | PLG (D5) | Rectangle + triangle composite |
| `rectangular_prism` | VOL (D1) | Isometric 3D box with l, w, h labels |
| `cylinder` | VOL (D2, D5) | Top ellipse with radius; side with height |
| `cone` | VOL (D3) | Dashed altitude and base radius labeled |
| `sphere` | VOL (D4) | Dashed equator + dashed radius line |
| `bar_chart` | DAT (D1, D2, D4, D5) | D4: one bar shown as "?" with dashed outline |
| `pie_chart` | DAT (D3) | Color-coded segments with legend + total |
| `number_line` | LNI (D1–D5), ABV (D3–D4) | Open/closed points, shading arrows for inequality direction |
| `scatter_plot` | SCA (D1–D5) | Data points + dashed line of best fit; auto-scaled axes |
| `box_plot` | STA (D4) | Whiskers, IQR box, median line, Q1/Med/Q3 labels |
| `two_way_table` | TWT (D1–D5) | Header row, row labels, highlight support for target cell |
| `parabola` | QFN (D1–D5) | Dynamic scaling, vertex dot + label, dashed axis of symmetry, optional roots |

**No diagram:** LEQ, LWP, SLE, QEQ, PCT, RAT, PRP, ABV (D1–D2), STA (D1–D3, D5), PRB, EXR, POL, SEQ, CMX

---

## Known Gaps (Low Priority)

| Item | Notes |
|---|---|
| Conic sections (ellipse, hyperbola) | Not on most SAT tests; parabolas covered via QFN |
| Histogram diagram | Would require a frequency-distribution statistics sub-type |
| Unit circle diagram | Full trig unit circle; current TRG uses right_triangle |
| Compound bar / stacked bar | Multi-variable data analysis not yet modeled |
| Systems of linear inequalities | Compound constraint problems |
| Inference / margin of error | Statistical sampling questions |
