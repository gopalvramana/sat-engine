# 07 — Business Model and Pricing

---

## ADR-033 — Pricing

| Plan | Price | Notes |
|------|-------|-------|
| Free | $0 | One full practice test, score report, no AI panel |
| Monthly | **$14.99/month** | Full access, unlimited tests, full AI panel |
| Annual | **$119.99/year** | 2 months free (~$10/month) |

**First test is always free — no credit card required.**

### Why $14.99
- 6x cheaper than Acely ($99–199/month) with better AI architecture
- Slightly cheaper than Whiz ($20/month) with deeper features
- Monthly recurring is better than one-time for a growing platform
- Price-sensitive Indian-American families can afford this
- Break-even requires only 5–10 paying students

### Why Free First Test (No Credit Card)
Acely's most-complained-about aspect is requiring a credit card for a 3-day trial. Removing this friction demonstrates confidence in the product and converts better.

**Status:** ✅ DECIDED

---

## ADR-034 — H1B Monetisation Strategy

**Decision:** Indian Private Limited company structure.

**Setup:**
- Family member in India as director
- CA in India handles incorporation (~₹10,000–23,000 setup, ~₹17,000–30,000/year compliance)
- Revenue flows to Indian company
- Stripe → Indian bank account

**Timeline:**
- Start company setup NOW — parallel to development
- Free validation phase during H1B period
- Monetise when company structure is active

**US immigration note:** Consult a US immigration lawyer about your specific H1B situation before activating revenue collection.

**After returning to India:** Structure simplifies significantly. You become director directly. No cross-border complexity.

**Status:** 🔄 IN PROGRESS — Start this week

---

## ADR-035 — Free Tier Design

**Decision:**
- One full 98-question practice test — completely free
- No credit card required
- Score report included
- AI panel NOT available in free tier
- Second test requires subscription
- Clear upgrade prompt after completing first test

**The conversion funnel:**
```
Student starts free test
→ Completes 98 questions (~2 hours invested)
→ Sees their score report + weak areas
→ Wants to understand WHY they got questions wrong
→ Clicks a tab → "Upgrade to unlock AI explanations"
→ $14.99/month is an easy decision at this point
```

**Status:** ✅ DECIDED

---

## ADR-036 — Competitive Positioning

**Decision:** Position as "the platform that teaches WHY, not just WHAT."

### What We Are NOT Saying
- ~~"Better than Acely"~~ — cannot claim at launch
- ~~"Cheapest option"~~ — price alone doesn't win
- ~~"Built for Indian students"~~ — too narrow, limits market

### What We ARE Saying
> "The SAT platform that teaches you WHY you got it wrong — not just what the right answer is. Practice like it's the real test. Learn like you have a personal tutor."

### Secondary Messages
- "Practice without AI. Learn with AI. Just like the real test."
- "AI that debates you, not just explains to you." (when Debate Mode launches)
- "Built by a parent who was frustrated with every existing platform."

### Target Students for Messaging
Students who have tried Acely or Khan Academy and found explanations circular or generic. They are already aware of the problem you're solving. They are looking for exactly what you built.

**Status:** ✅ DECIDED

---

## ADR-037 — Distribution Strategy

### Phase 1 — Launch (Month 4–6)

| Channel | How | Expected Result | Cost |
|---------|-----|----------------|------|
| **r/SAT** (400K+ members) | Genuine helpful posts about SAT strategy. Mention platform naturally. One DASA pathway post can get thousands of views. | High intent users. r/SAT actively seeks prep advice. | Free |
| **r/ApplyingToCollege** (800K+ members) | Share authentic story — parent who built this for his daughter | Reaches students AND parents | Free |
| **Indian parent Facebook groups** | DASA pathway content + platform | Parents share useful tools instantly in WhatsApp chains | Free |
| **LinkedIn** | Your professional story — 20-year engineer builds AI platform for daughter | NRI tech professionals with high-school children | Free |
| **Telugu/Indian associations** | Free webinar: "DASA pathway to Indian engineering colleges" | 20 attendees = 20 warm leads | Free |

### Phase 2 — Growth (Month 6+)
- School counselor outreach (high trust, multiplier effect)
- SAT tutor partnerships (they recommend to every student)
- SEO content — SAT tips, domain guides (compounds monthly)
- YouTube demos of AI panel in action (visual converts better than text)

### What NOT to Do at Launch
**No paid ads.** Zero reviews + zero social proof + zero brand = terrible ROI. Wait until you have 10+ testimonials and a proven score improvement story.

**Status:** ✅ DECIDED

---

## Revenue Projections

### Conservative Path (lean effort, steady growth)
| Month | Students | Monthly Revenue | Cumulative |
|-------|----------|----------------|------------|
| 4 (launch) | 10 | $150 | $150 |
| 5 | 25 | $375 | $525 |
| 6 | 50 | $750 | $1,275 |
| 8 | 100 | $1,499 | $4,000 |
| 10 | 150 | $2,249 | $8,000 |
| 12 | 200 | $2,998 | $14,000 |

### Base Path (one viral r/SAT moment)
| Month | Students | Monthly Revenue |
|-------|----------|----------------|
| 12 | 350 | $5,247 |
| 18 | 600 | $8,994 |
| 24 | 900 | $13,491 |
| 36 | 1,700 | $25,483 |

### The 0.1% Market Target
- 0.1% of 1.7M SAT takers = 1,700 students
- Revenue: **$25,483/month**
- Realistic timeline: **Year 3**
- Probability: **35–45%**

---

## Running From India — Financial Reality

| Metric | USA context | India context |
|--------|-------------|---------------|
| Level 2 ($2,000–4,000/mo) | Good side income | Financial independence |
| Level 3 ($8,000–15,000/mo) | Meaningful income | Life-changing |
| Team hire (part-time content) | $2,000–3,000/mo | $300–500/mo |
| CA + compliance | N/A | ~$500/year |

Going back to India does not hurt the business. The product is location-independent. It helps — lower costs, simpler company structure, H1B constraints removed, JEE market accessible.
