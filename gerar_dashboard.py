#!/usr/bin/env python3
"""
Gerador do Painel Executivo — Barco Hospital São João XXIII
=============================================================
Uso:
    python gerar_dashboard.py caminho/para/planilha.ods

Lê a planilha oficial (qualquer aba cujo nome contenha um ano de 4 dígitos,
ex: "2025", "2026", "2027"...), recalcula tudo, e gera um dashboard.html
pronto para publicar (Netlify, GitHub Pages, etc). Nenhuma edição de
código é necessária de um ano para o outro.
"""
import sys
import os
import json
import re
import argparse
from datetime import datetime
from parser import extract_all_years

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template.html")


import statistics


def run_quality_checks(all_expeditions, data_by_year):
    warnings = []

    for year, d in data_by_year.items():
        exps = d["expeditions"]
        if not exps:
            warnings.append(f"Ano {year}: nenhuma expedição válida encontrada.")
            continue

        # zero/blank totals
        for e in exps:
            if e["geral"] == 0:
                warnings.append(f"{year} · Expedição {e['n']} ({e['mun']}): Atendimento Geral está zerado.")
            if not e["mun"] or e["mun"].strip() == "":
                warnings.append(f"{year} · Expedição {e['n']}: nome de município vazio.")

        # outliers vs the year's own median (catches transcription-style errors)
        gerais = [e["geral"] for e in exps if e["geral"] > 0]
        if len(gerais) >= 3:
            med = statistics.median(gerais)
            for e in exps:
                if e["geral"] > 0 and (e["geral"] > med * 2.2 or e["geral"] < med * 0.35):
                    warnings.append(
                        f"{year} · Expedição {e['n']} ({e['mun']}): Atendimento Geral = {e['geral']:,} "
                        f"foge muito da mediana do ano ({med:,.0f}) — vale conferir na planilha."
                        .replace(",", ".")
                    )

        # duplicate expedition numbers within the same year
        seen = {}
        for e in exps:
            seen[e["n"]] = seen.get(e["n"], 0) + 1
        for n, count in seen.items():
            if count > 1:
                warnings.append(f"{year}: número de expedição {n} aparece {count} vezes (deveria ser único).")

        # internal consistency: Geral should equal Saúde + Alimentação (as verified in the source spreadsheet)
        for e in exps:
            expected = e["saude"] + e["alim"]
            if e["geral"] > 0 and abs(e["geral"] - expected) > max(2, e["geral"] * 0.02):
                warnings.append(
                    f"{year} · Expedição {e['n']} ({e['mun']}): Total Geral ({e['geral']}) não bate com "
                    f"Saúde + Alimentação ({expected}) — confira a planilha."
                )

        # date string year should match the expedition's actual year (catches typos in the source spreadsheet)
        for e in exps:
            if e.get("data"):
                found_years = re.findall(r'(20\d{2})', e["data"])
                if found_years and str(year) not in found_years:
                    warnings.append(
                        f"{year} · Expedição {e['n']} ({e['mun']}): data informada é \"{e['data']}\", "
                        f"que não contém o ano {year} — confira a planilha."
                    )

    return warnings


def build_dashboard(ods_path, output_path, proxy_url="", proxy_secret=""):
    if not os.path.isfile(ods_path):
        print(f"❌ Arquivo não encontrado: {ods_path}")
        sys.exit(1)

    print(f"📖 Lendo planilha: {ods_path}")
    data_by_year = extract_all_years(ods_path)

    if not data_by_year:
        print("❌ Nenhuma aba com ano válido (ex: 2025, 2026) foi encontrada na planilha.")
        sys.exit(1)

    all_expeditions = []
    specialties_by_year = {}
    exams_by_year = {}

    for year in sorted(data_by_year.keys()):
        d = data_by_year[year]
        all_expeditions.extend(d["expeditions"])
        specialties_by_year[str(year)] = d["specialties"]
        exams_by_year[str(year)] = d["exams"]
        total_geral = sum(e["geral"] for e in d["expeditions"])
        print(f"   ✓ {year}: {len(d['expeditions'])} expedições · "
              f"{len(d['specialties'])} especialidades · {len(d['exams'])} tipos de exame · "
              f"{total_geral:,} atendimentos gerais".replace(",", "."))

    if not os.path.isfile(TEMPLATE_PATH):
        print(f"❌ Arquivo de template não encontrado: {TEMPLATE_PATH}")
        sys.exit(1)

    print()
    print("🔍 Verificando qualidade dos dados...")
    warnings = run_quality_checks(all_expeditions, data_by_year)
    if warnings:
        print(f"⚠️  {len(warnings)} ponto(s) de atenção encontrados (o arquivo será gerado mesmo assim):")
        for w in warnings:
            print(f"   • {w}")
    else:
        print("   ✓ Nenhuma inconsistência encontrada.")

    template = open(TEMPLATE_PATH, encoding="utf-8").read()
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = template
    html = html.replace("__ALL_EXPEDITIONS__", json.dumps(all_expeditions, ensure_ascii=False))
    html = html.replace("__SPECIALTIES_BY_YEAR__", json.dumps(specialties_by_year, ensure_ascii=False))
    html = html.replace("__EXAMS_BY_YEAR__", json.dumps(exams_by_year, ensure_ascii=False))
    html = html.replace("__GENERATED_AT__", generated_at)
    html = html.replace("__PROXY_URL__", proxy_url)
    html = html.replace("__PROXY_SECRET__", proxy_secret)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    total_geral_all = sum(e["geral"] for e in all_expeditions)
    print()
    print(f"✅ Painel gerado com sucesso: {output_path}")
    print(f"   Total: {len(all_expeditions)} expedições · {total_geral_all:,} atendimentos gerais".replace(",", "."))
    print(f"   Anos incluídos: {', '.join(str(y) for y in sorted(data_by_year.keys()))}")
    print(f"   Gerado em: {generated_at}")
    if proxy_url:
        print(f"   Assistente de IA: conectado ao proxy ({proxy_url})")
    else:
        print(f"   Assistente de IA: modo local (sem proxy configurado — use --proxy-url para ativar)")
    print()
    print(f"➡  Agora é só publicar o {output_path} (ex: arrastar a pasta no https://app.netlify.com/drop)")


if __name__ == "__main__":
    parser_args = argparse.ArgumentParser(description="Gera o painel executivo a partir da planilha de expedições.")
    parser_args.add_argument("planilha", nargs="?", default="EXPEDICOES_BHSJXXIII_2025_2026.ods",
                              help="Caminho para o arquivo .ods (padrão: EXPEDICOES_BHSJXXIII_2025_2026.ods na mesma pasta)")
    parser_args.add_argument("-o", "--output", default="index.html",
                              help="Nome do arquivo de saída (padrão: index.html, pronto para publicar sem precisar renomear)")
    parser_args.add_argument("--proxy-url", default="https://painel-bhsj23.alsf.workers.dev",
                              help="URL do Cloudflare Worker (veja worker.js) para ativar a IA completa. "
                                   "Use --proxy-url \"\" para gerar sem IA de proxy (só o motor local).")
    parser_args.add_argument("--proxy-secret", default="",
                              help="Senha compartilhada com o Worker (DASHBOARD_SECRET) para proteger o proxy")
    args = parser_args.parse_args()
    build_dashboard(args.planilha, args.output, args.proxy_url, args.proxy_secret)
