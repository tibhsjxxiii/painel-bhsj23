# Compare the committed index.html against a freshly generated one from the real .ods
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_json_vars(html):
    """Extract all injected JSON variables from a dashboard HTML."""
    vars_to_extract = {
        'ALL_EXPEDITIONS': r'ALL_EXPEDITIONS\s*=\s*(?:window\.ALL_EXPEDITIONS\s*=\s*)?(\[.*?\]);',
        'SPECIALTIES_BY_YEAR': r'SPECIALTIES_BY_YEAR\s*=\s*(\{.*?\}\});',
        'EXAMS_BY_YEAR': r'EXAMS_BY_YEAR\s*=\s*(\{.*?\}\});',
        'ANNUAL_PATIENT_STATS': r'ANNUAL_PATIENT_STATS\s*=\s*(\{.*?\}\});',
        'ANNUAL_DAYS_STATS': r'ANNUAL_DAYS_STATS\s*=\s*(\{.*?\}\});',
        'NAVIGATION_DATA': r'NAVIGATION_DATA\s*=\s*(\{.*?\}\});',
        'GENERATED_AT': r'GENERATED_AT\s*=\s*"([^"]*)";',
        'PROXY_URL': r'PROXY_URL\s*=\s*"([^"]*)";',
        'PROXY_SECRET': r'PROXY_SECRET\s*=\s*"([^"]*)";',
    }
    extracted = {}
    for name, pattern in vars_to_extract.items():
        m = re.search(pattern, html, re.DOTALL)
        if not m:
            print(f"[MISSING] Variable {name} not found")
            continue
        if name in ('GENERATED_AT', 'PROXY_URL', 'PROXY_SECRET'):
            extracted[name] = m.group(1)
        else:
            try:
                extracted[name] = json.loads(m.group(1))
            except Exception as e:
                print(f"[PARSE ERROR] {name}: {e}")
                extracted[name] = None
    return extracted

def main():
    with open('index.html', 'r', encoding='utf-8') as f:
        committed = f.read()
    with open('regenerated_test.html', 'r', encoding='utf-8') as f:
        regenerated = f.read()

    committed_data = extract_json_vars(committed)
    regenerated_data = extract_json_vars(regenerated)

    print("=== COMPARING COMMITTED INDEX.HTML vs FRESHLY GENERATED FROM REAL .ODS ===\n")

    all_ok = True
    for name in ['ALL_EXPEDITIONS', 'SPECIALTIES_BY_YEAR', 'EXAMS_BY_YEAR',
                 'ANNUAL_PATIENT_STATS', 'ANNUAL_DAYS_STATS', 'NAVIGATION_DATA',
                 'GENERATED_AT', 'PROXY_URL', 'PROXY_SECRET']:
        c = committed_data.get(name)
        r = regenerated_data.get(name)

        if name == 'GENERATED_AT':
            # Timestamp will differ - just check both exist
            print(f"GENERATED_AT  -> committed: {c} | regenerated: {r}")
            continue

        if c == r:
            print(f"✅ {name}: IDENTICAL ({len(c) if isinstance(c, (list, dict)) else c})")
        else:
            all_ok = False
            print(f"❌ {name}: DIFFERS!")
            if isinstance(c, (list, dict)) and isinstance(r, (list, dict)):
                if isinstance(c, list):
                    print(f"   committed: {len(c)} items, regenerated: {len(r)} items")
                    # Find differing items
                    if len(c) == len(r):
                        diffs = [i for i, (a, b) in enumerate(zip(c, r)) if a != b]
                        print(f"   Differing items: {len(diffs)}")
                        for i in diffs[:5]:
                            print(f"   - Item {i}: committed={c[i]}")
                            print(f"             regenerated={r[i]}")
                else:
                    for k in set(list(c.keys()) + list(r.keys())):
                        if c.get(k) != r.get(k):
                            print(f"   - Key '{k}': committed={c.get(k)} vs regenerated={r.get(k)}")

    print("\n" + "="*70)
    if all_ok:
        print("✅ RESULT: The committed index.html is 100% in sync with the real .ods spreadsheet.")
    else:
        print("❌ RESULT: The committed index.html is OUT OF SYNC with the .ods spreadsheet!")
    print("="*70)

if __name__ == '__main__':
    main()