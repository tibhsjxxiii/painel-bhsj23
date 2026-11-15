# Script de Verificação Cruzada (Menu para Menu)
import json
import re
import sys

def verify():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Extrai o JSON principal
    m_exp = re.search(r'ALL_EXPEDITIONS\s*=\s*(?:window\.ALL_EXPEDITIONS\s*=\s*)?(\[.*?\]);', html, re.DOTALL)
    exps = json.loads(m_exp.group(1)) if m_exp else []

    # 1. Total Geral vs Menus (Comparativo, Especialidades, Exames)
    total_geral = sum(e['geral'] for e in exps)
    total_saude = sum(e['saude'] for e in exps)
    total_alim = sum(e['alim'] for e in exps)

    print(f"Total Geral de Atendimentos: {total_geral:,}")
    print(f"Soma Saúde + Alimentação: {total_saude + total_alim:,}")

    # 2. Verificar Especialidades
    # A soma das consultas médicas deve bater com a soma das especialidades registradas
    total_consultas = sum(e['consultas'] for e in exps)
    # Somar todas as especialidades em todas as exps
    total_specs_in_exps = sum(sum(e['spec'].values()) for e in exps)

    print(f"Total de Consultas (ALL_EXPEDITIONS): {total_consultas:,}")
    print(f"Total somado de Especialidades individuais: {total_specs_in_exps:,}")

    # 3. Verificar Exames
    total_exames = sum(e['exames'] for e in exps)
    total_exams_in_exps = sum(sum(e['exam'].values()) for e in exps)

    print(f"Total de Exames (ALL_EXPEDITIONS): {total_exames:,}")
    print(f"Total somado de Exames individuais: {total_exams_in_exps:,}")

    # Validação cruzada de menus
    print("\n--- Validação de Cruzamento de Menus ---")
    if total_consultas == total_specs_in_exps:
        print("✅ Menu 'Especialidades' está sincronizado com os dados de 'Consultas'.")
    else:
        print("❌ [ERRO] Menu 'Especialidades' diverge da coluna de Consultas!")

    if total_exames == total_exams_in_exps:
        print("✅ Menu 'Exames' está sincronizado com os dados de 'Exames Totais'.")
    else:
        print("❌ [ERRO] Menu 'Exames' diverge da coluna de Exames Totais!")

verify()
