import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: data_analysis ──────────────────────────────────────────────────

def gen_data_analysis(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    TOPICS = ["Math", "Science", "English", "History", "Art"]
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    COLORS = ["Red", "Blue", "Green", "Yellow"]

    for _ in range(100):
        if difficulty == 1:
            # Bar chart: read one specific bar value
            cats = rng_obj.sample(TOPICS, 4)
            vals = [rng_obj.randint(10, 80) for _ in cats]
            target = rng_obj.randint(0, len(cats)-1)
            params = {"cats": cats, "vals": vals, "target": target, "ask": "read"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(vals[target])
            diag = {"type": "bar_chart", "categories": cats, "values": vals,
                    "ylabel": "Students", "highlight": target}
            return _dat(1, params, ph, ans, diag,
                        make_distractors(ans, [str(vals[target]+10), str(vals[target]-10),
                                               str(max(vals)), str(min(vals))]),
                        ctx=f"Read the bar chart. The bar for '{cats[target]}' has height {vals[target]}. The answer is {ans}.")

        elif difficulty == 2:
            # Bar chart: find the difference between max and min
            cats = rng_obj.sample(TOPICS, 4)
            vals = [rng_obj.randint(10, 90) for _ in cats]
            while max(vals) - min(vals) < 15:
                vals = [rng_obj.randint(10, 90) for _ in cats]
            diff = max(vals) - min(vals)
            params = {"cats": cats, "vals": vals, "ask": "max_minus_min"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(diff)
            diag = {"type": "bar_chart", "categories": cats, "values": vals,
                    "ylabel": "Students"}
            return _dat(2, params, ph, ans, diag,
                        make_distractors(ans, [str(max(vals)), str(min(vals)),
                                               str(diff+10), str(diff-5)]),
                        ctx=f"Find max minus min in the bar chart. Max={max(vals)}, min={min(vals)}, difference={diff}.")

        elif difficulty == 3:
            # Pie chart: given total N and a segment percentage, find the count
            total = rng_obj.choice([100, 200, 400, 500])
            segs = [rng_obj.choice([10, 15, 20, 25, 30]) for _ in range(4)]
            # Normalize to sum to 100
            s = sum(segs)
            segs = [round(x * 100 / s) for x in segs]
            segs[-1] = 100 - sum(segs[:-1])
            if any(v <= 0 for v in segs): continue
            target = rng_obj.randint(0, len(segs)-1)
            count = total * segs[target] // 100
            labels = rng_obj.sample(COLORS, len(segs))
            params = {"total": total, "segs": segs, "labels": labels, "target": target}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(count)
            diag = {"type": "pie_chart",
                    "segments": [{"label": lbl, "value": v}
                                  for lbl, v in zip(labels, segs)],
                    "total": total, "highlight": target}
            return _dat(3, params, ph, ans, diag,
                        make_distractors(ans, [str(count+total//10), str(count-total//10),
                                               str(segs[target]), str(total//4)]),
                        ctx=f"Pie chart total={total}. Segment '{labels[target]}' = {segs[target]}%. Count = {total}×{segs[target]}/100 = {count}.")

        elif difficulty == 4:
            # Bar chart: given total and 3 of 4 bars, find the missing bar
            cats = rng_obj.sample(TOPICS, 4)
            vals = [rng_obj.randint(15, 60) for _ in cats]
            total = sum(vals)
            missing_idx = rng_obj.randint(0, 3)
            missing_val = vals[missing_idx]
            known_total = total - missing_val
            params = {"cats": cats, "vals": vals, "missing_idx": missing_idx, "total": total}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(missing_val)
            shown_vals = vals[:]
            shown_vals[missing_idx] = 0  # 0 means the bar is "?" / unknown
            diag = {"type": "bar_chart", "categories": cats, "values": shown_vals,
                    "ylabel": "Count", "missing": missing_idx, "total": total}
            return _dat(4, params, ph, ans, diag,
                        make_distractors(ans, [str(missing_val+10), str(total//4),
                                               str(missing_val-5), str(known_total)]),
                        ctx=f"Bar chart: total={total}, three bars known (sum={known_total}). Missing bar = {total}-{known_total} = {missing_val}.")

        elif difficulty == 5:
            # Bar chart: calculate percentage one category is of total
            cats = rng_obj.sample(MONTHS[:4], 4)
            vals = [rng_obj.randint(10, 40) for _ in cats]
            total = sum(vals)
            target = rng_obj.randint(0, len(cats)-1)
            pct = round(vals[target] * 100 / total)
            if pct <= 0 or pct >= 100: continue
            params = {"cats": cats, "vals": vals, "target": target, "ask": "percent"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(pct)
            diag = {"type": "bar_chart", "categories": cats, "values": vals,
                    "ylabel": "Sales", "highlight": target}
            return _dat(5, params, ph, ans, diag,
                        make_distractors(ans, [str(vals[target]), str(pct+10),
                                               str(pct-10), str(100-pct)]),
                        ctx=f"Bar chart total={total}. '{cats[target]}' bar={vals[target]}. Percentage = {vals[target]}/{total}×100 ≈ {pct}%.")

        else:
            raise NotImplementedError(f"data_analysis d{difficulty} not implemented")
    raise RuntimeError(f"Could not generate unique params for data_analysis d{difficulty}")


def _dat(d, params, ph, ans, diag, distractors, ctx=""):
    return {"skill": "data_analysis", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}
