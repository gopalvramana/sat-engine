# SymPy Pipeline — Coverage Reference

Last updated: 2026-04-16  
Source of truth: `sat-engine/scripts/math_engine.py`

---

## Question Types & Difficulty Levels by Topic

All 15 topics implement **D1–D5** fully. D6–D7 are not implemented (fall back to D4 in the CLI).

| Topic | Code | Domain | D1 | D2 | D3 | D4 | D5 | SPR Difficulties |
|---|---|---|---|---|---|---|---|---|
| Linear equations (1 variable) | LEQ | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D3 (30%), D4 (40%) |
| Linear equation word problems | LWP | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Systems of linear equations | SLE | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Linear functions | LFN | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Quadratic equations | QEQ | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D4 (40%) |
| Percentages | PCT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Ratios & rates | RAT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Proportional relationships | PRP | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Pythagorean theorem | PYT | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | D3 (40%), D4 (40%) |
| Area (2D shapes) | ARA | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | D4 (40%) |
| Coordinate geometry | CGE | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Circles | CIR | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Volume (3D shapes) | VOL | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Plane geometry | PLG | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Data analysis | DAT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |

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

### Data Analysis (DAT)
| D | Chart Type | What is Asked |
|---|---|---|
| D1 | Bar chart | Read a specific bar value |
| D2 | Bar chart | Max − min difference |
| D3 | Pie chart | Convert % to count (count = total × pct / 100) |
| D4 | Bar chart (missing bar) | Find missing value (missing = total − known) |
| D5 | Bar chart | Calculate one category as % of total |

---

## Diagram Types by Topic

| Diagram Type | Topics | Notes |
|---|---|---|
| `coordinate_plane` | LFN (D1–D5), CGE (D1–D5) | Supports: function line, data points, highlight_point, hideLabel flag |
| `right_triangle` | PYT (D1–D5) | Shows legs and hypotenuse; missing value shown as "?" |
| `rectangle` | ARA (D1, D4) | Shows length × width; D4 has width = "?" |
| `triangle` | ARA (D2) | Shows base and height with dashed altitude |
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

**No diagram:** LEQ, LWP, SLE, QEQ, PCT, RAT, PRP

---

## Not Supported — Missing SAT Topics

These are tested on the SAT but not yet implemented in the SymPy pipeline:

| Topic | SAT Domain | Priority |
|---|---|---|
| Statistics (mean, median, mode, IQR, std dev) | PSDA | High |
| Scatterplots & line of best fit | PSDA | High |
| Two-way tables (joint/marginal/conditional frequency) | PSDA | High |
| Probability (simple, compound, conditional) | PSDA | High |
| Inequalities (linear, compound, systems) | Algebra | High |
| Absolute value equations & inequalities | Algebra | Medium |
| Exponents & radicals (laws, rational exponents) | Algebra | Medium |
| Polynomial operations (FOIL, factoring, long division) | Algebra | Medium |
| Special triangles (30-60-90, 45-45-90) | Geometry | Medium |
| Trigonometry (sin, cos, tan, SOHCAHTOA) | Geometry | Medium |
| Sequences & series (arithmetic, geometric) | Algebra | Low |
| Complex numbers | Algebra | Low |
| Conic sections (parabola, ellipse, hyperbola) | Geometry | Low |

---

## Not Supported — Missing Diagram Types

These diagrams would be needed if the missing topics above were implemented:

| Diagram | Needed For |
|---|---|
| Number line | Inequalities, absolute value |
| Scatter plot | Regression, correlation |
| Histogram | Statistics (frequency distributions) |
| Box plot / whisker | IQR, quartiles, outliers |
| Two-way table | Probability, conditional frequency |
| 30-60-90 / 45-45-90 triangle | Special triangle problems |
| Unit circle | Trigonometry |
| Parabola (coordinate plane + vertex) | Quadratic functions graphed |
| Compound bar / stacked bar | Multi-variable data analysis |
