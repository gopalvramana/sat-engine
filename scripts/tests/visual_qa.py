#!/usr/bin/env python3
"""
Visual QA for SAT math generators.
Generates 1 question per (skill, template, variant), renders it in headless
Chromium, screenshots it, and sends to Claude Vision for math validation.

Usage:
  python3 scripts/tests/visual_qa.py                        # all variant-driven skills
  python3 scripts/tests/visual_qa.py --skill=linear_eq_one_var
  python3 scripts/tests/visual_qa.py --skill=linear_eq_one_var,linear_functions
"""
import argparse, base64, html as html_lib, json, subprocess, sys, datetime
from pathlib import Path

SAT_ENGINE_DIR = Path(__file__).parent.parent.parent
MATH_ENGINE    = SAT_ENGINE_DIR / "scripts" / "math_engine.py"
PREVIEW_HTML   = SAT_ENGINE_DIR / "src" / "main" / "resources" / "static" / "admin" / "question-preview.html"
OUTPUT_DIR     = Path(__file__).parent / "test-output"

VARIANT_DRIVEN_SKILLS = [
    "linear_eq_one_var",
    "linear_eq_two_var",
    "linear_inequalities",
    "systems_linear_eq",
    "linear_functions",
    "equivalent_expressions",
    "nonlinear_equations",
]

# Used when exactStem is present — Claude can solve independently
VALIDATION_PROMPT_FULL = """You are an expert SAT math question validator. A rendered question card is shown.
The correct answer is highlighted in green with a ✓ CORRECT badge.
SPR questions show "✓ Answer: X" with no choices — DISTRACTORS_VALID is always YES for those.

Work through these steps, then end with the result line:

1. Solve the problem yourself from the question stem shown.
2. Does the highlighted answer match your solution? (MATH_CORRECT)
3. For each non-highlighted choice, verify it is genuinely wrong and not accidentally correct. (DISTRACTORS_VALID). Also NO if any distractor is absurd or a duplicate.
4. Is there enough information to solve the problem? (STEM_COMPLETE)
5. Any broken LaTeX, clipped diagram, or garbled text? (RENDERING_OK)

After your reasoning, output EXACTLY this as the final line:
MATH_CORRECT:YES|DISTRACTORS_VALID:YES|STEM_COMPLETE:YES|RENDERING_OK:YES"""

# Used when only questionContext is available — skip math checks, only validate rendering
VALIDATION_PROMPT_RENDER_ONLY = """You are reviewing a rendered SAT math question card (pre-narration stage).
The card shows an internal context note (blue border) — this is generator context, not a student-facing stem.
The correct answer is highlighted in green with a ✓ CORRECT badge.

Check only these two things:

1. STEM_COMPLETE — Does the context note contain enough math to understand what is being asked?
2. RENDERING_OK  — No broken LaTeX, no clipped diagram, no garbled text?

Mark MATH_CORRECT:SKIP and DISTRACTORS_VALID:SKIP (math validation requires a full stem).

After your reasoning, output EXACTLY this as the final line:
MATH_CORRECT:SKIP|DISTRACTORS_VALID:SKIP|STEM_COMPLETE:YES|RENDERING_OK:YES"""


def get_variants(skill: str) -> dict:
    """Return {template: (difficulty, [variants])} across all difficulty levels."""
    combined = {}
    for diff in (1, 2, 3):
        r = subprocess.run(
            ["python3", str(MATH_ENGINE), "--skill", skill,
             "--list-variants", f"--difficulty={diff}"],
            capture_output=True, text=True, cwd=str(SAT_ENGINE_DIR)
        )
        if r.returncode != 0 or not r.stdout.strip():
            continue
        try:
            data = json.loads(r.stdout)
        except Exception:
            continue
        for tpl, variants in data.items():
            combined[tpl] = (diff, variants)
    return combined


def generate_question(skill: str, template: str, variant: str,
                      difficulty: int = 3, seed: int = 42):
    r = subprocess.run(
        ["python3", str(MATH_ENGINE),
         "--skill", skill, "--template", template, "--variant", variant,
         "--difficulty", str(difficulty), "--count", "1", "--seed", str(seed)],
        capture_output=True, text=True, cwd=str(SAT_ENGINE_DIR)
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        data = json.loads(r.stdout)
        # If generator returned an error dict rather than a question, treat as failure
        if "error" in data and "verifiedAnswer" not in data:
            return None
        return data
    except Exception:
        return None


def parse_validation(text: str):
    """Find the MATH_CORRECT:YES|... result line anywhere in the response."""
    checks = {}
    result_line_idx = -1

    lines = text.strip().split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if '|' not in stripped or ':' not in stripped:
            continue
        candidate = {}
        for part in stripped.split('|'):
            if ':' in part:
                k, v = part.split(':', 1)
                k, v = k.strip(), v.strip().upper()
                if v in ('YES', 'NO', 'SKIP') and k.replace('_', '').isalpha():
                    candidate[k] = v   # store string: 'YES', 'NO', 'SKIP'
        if len(candidate) >= 3:
            checks = candidate
            result_line_idx = i
            break

    # Issues = any lines after the result line that flag a problem
    issues_lines = [l.strip() for l in lines[result_line_idx+1:] if l.strip()] if result_line_idx >= 0 else []
    issues = '\n'.join(issues_lines)
    return checks, issues


def run_qa(skills: list[str], seed: int = 42):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed.\nRun: pip install playwright && playwright install chromium")
        sys.exit(1)
    try:
        import anthropic
        client = anthropic.Anthropic()
    except ImportError:
        print("ERROR: anthropic not installed.\nRun: pip install anthropic")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    preview_url = f"file://{PREVIEW_HTML.resolve()}"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 620, "height": 900})
        page.goto(preview_url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(500)  # let KaTeX CDN start loading

        for skill in skills:
            variants_map = get_variants(skill)
            if not variants_map:
                print(f"  SKIP {skill}: --list-variants returned nothing for any difficulty")
                continue

            for template, (difficulty, variants) in variants_map.items():
                for variant in variants:
                    label = f"{skill}/d{difficulty}/{template}/{variant}"

                    # 1. Generate
                    q = generate_question(skill, template, variant, difficulty, seed)
                    if q is None:
                        print(f"  SKIP  {label}  (generation failed)")
                        results.append({"label": label, "status": "skip", "error": "generation failed"})
                        continue

                    # 2. Render in browser + screenshot
                    page.evaluate("q => window.renderQuestion(q)", q)
                    page.wait_for_timeout(700)   # KaTeX + SVG settle
                    png_bytes = page.locator("#question-card").screenshot()

                    # 3. Claude Vision validation
                    has_stem = bool(q.get("exactStem"))
                    prompt = VALIDATION_PROMPT_FULL if has_stem else VALIDATION_PROMPT_RENDER_ONLY
                    b64 = base64.b64encode(png_bytes).decode()
                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                                {"type": "text", "text": prompt}
                            ]
                        }]
                    )
                    raw = response.content[0].text
                    checks, issues = parse_validation(raw)

                    # SKIP = not applicable (no exactStem); only YES/NO determine pass/fail
                    passed = all(v != 'NO' for v in checks.values()) if checks else False
                    if not checks:
                        print(f"  WARN parse failed — raw: {raw[:120]!r}")
                    icon = "✓" if passed else "✗"
                    print(f"  {icon}  {label}")
                    if issues:
                        for line in issues.splitlines():
                            if line.strip():
                                print(f"       → {line.strip()}")

                    results.append({
                        "label":    label,
                        "skill":    skill,
                        "template": template,
                        "variant":  variant,
                        "status":   "pass" if passed else "fail",
                        "checks":   checks,
                        "issues":   issues,
                        "screenshot": b64,
                        "question": q,
                        "raw":      raw,
                    })

        browser.close()

    report_path = write_report(results)
    return report_path


def write_report(results: list) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / f"report_{ts}.html"

    total   = len(results)
    passed  = sum(1 for r in results if r.get("status") == "pass")
    failed  = sum(1 for r in results if r.get("status") == "fail")
    skipped = sum(1 for r in results if r.get("status") == "skip")

    cards_html = ""
    for r in results:
        status = r.get("status", "skip")
        border = "#22c55e" if status == "pass" else "#ef4444" if status == "fail" else "#d1d5db"
        bg     = "#f0fdf4" if status == "pass" else "#fef2f2" if status == "fail" else "#f9fafb"
        icon   = "✓" if status == "pass" else "✗" if status == "fail" else "–"
        icon_color = "#16a34a" if status == "pass" else "#dc2626" if status == "fail" else "#9ca3af"

        checks_html = ""
        for k, v in (r.get("checks") or {}).items():
            if v == 'YES':
                c, sym = "#16a34a", "✓"
            elif v == 'NO':
                c, sym = "#dc2626", "✗"
            else:  # SKIP
                c, sym = "#9ca3af", "–"
            checks_html += f'<span style="color:{c};font-size:11px;margin-right:10px">{sym} {html_lib.escape(k)}</span>'

        issues_html = ""
        if r.get("issues"):
            issues_html = f'<div style="color:#dc2626;font-size:12px;margin-top:6px;line-height:1.4">{html_lib.escape(r["issues"])}</div>'

        img_html = ""
        if r.get("screenshot"):
            img_html = (
                f'<div style="margin-top:10px">'
                f'<img src="data:image/png;base64,{r["screenshot"]}" '
                f'style="width:100%;border-radius:6px;border:1px solid #e5e7eb;cursor:zoom-in" '
                f'onclick="this.style.width=this.style.width===\'100%\'?\'180%\':\'100%\'" '
                f'title="Click to zoom"></div>'
            )

        error_html = f'<div style="color:#9ca3af;font-size:12px">{html_lib.escape(r.get("error",""))}</div>' if r.get("error") else ""

        cards_html += f"""
        <div style="border:1.5px solid {border};border-radius:10px;padding:14px 16px;background:{bg}">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span style="font-size:16px;font-weight:800;color:{icon_color}">{icon}</span>
            <span style="font-size:12px;font-weight:700;color:#374151;word-break:break-all">{html_lib.escape(r['label'])}</span>
          </div>
          {checks_html}
          {issues_html}
          {error_html}
          {img_html}
        </div>"""

    pass_pct = round(passed / total * 100) if total else 0

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Visual QA Report {ts}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f3f4f6; padding: 24px; }}
    h1 {{ font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 16px; }}
    .summary {{
      background: white; border-radius: 10px; padding: 16px 24px;
      margin-bottom: 24px; display: flex; gap: 40px; align-items: center;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .stat {{ text-align: center; }}
    .stat-n {{ font-size: 30px; font-weight: 800; line-height: 1.1; }}
    .stat-l {{ font-size: 11px; color: #6b7280; margin-top: 2px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }}
  </style>
</head>
<body>
  <h1>Visual QA Report &mdash; {ts}</h1>
  <div class="summary">
    <div class="stat"><div class="stat-n" style="color:#374151">{total}</div><div class="stat-l">Total</div></div>
    <div class="stat"><div class="stat-n" style="color:#16a34a">{passed}</div><div class="stat-l">Passed</div></div>
    <div class="stat"><div class="stat-n" style="color:#dc2626">{failed}</div><div class="stat-l">Failed</div></div>
    <div class="stat"><div class="stat-n" style="color:#9ca3af">{skipped}</div><div class="stat-l">Skipped</div></div>
    <div class="stat"><div class="stat-n" style="color:#6366f1">{pass_pct}%</div><div class="stat-l">Pass rate</div></div>
  </div>
  <div class="grid">{cards_html}</div>
</body>
</html>"""

    out.write_text(page, encoding="utf-8")
    print(f"\nReport saved: {out}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Visual QA for SAT math generators")
    parser.add_argument("--skill", help="Comma-separated skill keys (default: all variant-driven)")
    parser.add_argument("--seed",  type=int, default=42, help="Random seed for generation (default: 42)")
    args = parser.parse_args()

    skills = [s.strip() for s in args.skill.split(",")] if args.skill else VARIANT_DRIVEN_SKILLS

    print(f"Visual QA — {len(skills)} skill(s): {', '.join(skills)}")
    print(f"Preview: {PREVIEW_HTML}")
    print()

    run_qa(skills, seed=args.seed)


if __name__ == "__main__":
    main()
