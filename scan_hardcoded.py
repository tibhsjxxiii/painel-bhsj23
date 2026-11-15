# Varredura de valores hardcoded no template.html
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

def run():
    with open('index.html','r',encoding='utf-8') as f:
        html=f.read()

    m=re.search(r'ALL_EXPEDITIONS\s*=\s*(?:window\.ALL_EXPEDITIONS\s*=\s*)?(\[.*?\]);',html,re.DOTALL)
    exps=json.loads(m.group(1))

    y25=[e for e in exps if e.get('year')==2025]
    y26=[e for e in exps if e.get('year')==2026]

    real={
        'kpi-total-2025':sum(e['geral'] for e in y25),
        'kpi-total-2026':sum(e['geral'] for e in y26),
        'kpi-media-2025':round(sum(e['geral'] for e in y25)/len(y25)),
        'kpi-media-2026':round(sum(e['geral'] for e in y26)/len(y26)),
        'kpi-pac-2025':sum(e['pacientes'] for e in y25),
        'kpi-pac-2026':sum(e['pacientes'] for e in y26),
        'kpi-dias-2025':round(sum(e['diasAtendimento'] for e in y25),1),
        'kpi-dias-2026':round(sum(e['diasAtendimento'] for e in y26),1),
    }

    # find the template's hardcoded values
    print("=== VARREDURA DE VALORES HARDCODED NO TEMPLATE ===\n")
    errs=0
    for k,realv in real.items():
        pat=re.compile(r'id="'+k+r'">([^<]*)<')
        ms=pat.findall(html)
        if not ms:
            print(f"[AVISO] {k}: elemento não encontrado")
            continue
        hv=ms[0]
        hv_num=float(hv.replace('.','').replace(',','.')) if ',' in hv or '.' in hv else float(hv)
        real_num=float(realv)
        if abs(hv_num-real_num)>0.01:
            errs+=1
            print(f"❌ {k}: HARDCODED='{hv}'  REAL='{realv}'  (DIFERENCA)")
        else:
            print(f"✅ {k}: hardcoded='{hv}'  REAL='{realv}'  OK")

    # check the "N expedições" text divs
    print("\n=== TEXTOS 'N expedições' HARDCODED ===\n")
    for line in html.split('\n'):
        if 'expedições' in line.lower() and ('<div' in line or 'div>' in line) and 'style="font-size: 0.75rem' in line:
            print("  "+line.strip())

    print(f"\nTotal de erros encontrados: {errs}")

run()