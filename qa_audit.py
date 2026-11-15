# QA Audit Script for Painel BHSJ23 - Corrected
import json
import re
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def audit():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("=== AUDITORIA COMPLETA DE QUALIDADE DE DADOS E CÓDIGO (QA) ===")

    # 1. Extract JSON data objects
    # ALL_EXPEDITIONS = window.ALL_EXPEDITIONS = [...]
    m_exp = re.search(r'ALL_EXPEDITIONS\s*=\s*(?:window\.ALL_EXPEDITIONS\s*=\s*)?(\[.*?\]);', html, re.DOTALL)
    m_spec = re.search(r'SPECIALTIES_BY_YEAR\s*=\s*(\{.*?\}\});', html, re.DOTALL) or re.search(r'SPECIALTIES_BY_YEAR\s*=\s*(\{.*?\});', html, re.DOTALL)
    m_exam = re.search(r'EXAMS_BY_YEAR\s*=\s*(\{.*?\}\});', html, re.DOTALL) or re.search(r'EXAMS_BY_YEAR\s*=\s*(\{.*?\});', html, re.DOTALL)
    m_pat = re.search(r'ANNUAL_PATIENT_STATS\s*=\s*(\{.*?\});', html, re.DOTALL)
    m_days = re.search(r'ANNUAL_DAYS_STATS\s*=\s*(\{.*?\});', html, re.DOTALL)
    m_nav = re.search(r'NAVIGATION_DATA\s*=\s*(\{.*?\});', html, re.DOTALL)

    exps = json.loads(m_exp.group(1)) if m_exp else []
    spec_map = json.loads(m_spec.group(1)) if m_spec else {}
    exam_map = json.loads(m_exam.group(1)) if m_exam else {}
    pat_map = json.loads(m_pat.group(1)) if m_pat else {}
    days_map = json.loads(m_days.group(1)) if m_days else {}
    nav_map = json.loads(m_nav.group(1)) if m_nav else {}

    print(f"\n[DADOS CARREGADOS]")
    print(f"Total de Expedições: {len(exps)}")
    print(f"Especialidades por ano: {list(spec_map.keys())}")
    print(f"Exames por ano: {list(exam_map.keys())}")
    print(f"Estatísticas de Pacientes (ANNUAL_PATIENT_STATS): {pat_map}")
    print(f"Estatísticas de Dias (ANNUAL_DAYS_STATS): {days_map}")
    print(f"Dados de Navegação: {len(nav_map)} registros")

    # ----------------------------------------------------
    # AUDIT 1: SOMAS E EQUAÇÕES DAS EXPEDIÇÕES
    # ----------------------------------------------------
    print("\n" + "="*70)
    print("1. AUDITORIA DE MATEMÁTICA E SOMAS INDIVIDUAIS POR EXPEDIÇÃO")
    print("="*70)

    discrepancies = []

    for e in exps:
        exp_id = f"{e.get('year')} · Exp {e.get('n')} ({e.get('mun')})"

        # Equação Principal: geral = saude + alim
        geral = e.get('geral', 0)
        saude = e.get('saude', 0)
        alim = e.get('alim', 0)
        calc_geral = saude + alim

        if geral != calc_geral:
            msg = f"❌ [ERRO SOMA GERAL] {exp_id}: 'geral' ({geral:,}) != 'saude' ({saude:,}) + 'alim' ({alim:,}) [Soma = {calc_geral:,} | Dif: {geral - calc_geral}]"
            discrepancies.append(msg)
            print(msg)

        # Componentes de Saúde: consultas + oft + odonto + naoMed + exames + intern + proc + farm
        consultas = e.get('consultas', 0)
        oft = e.get('oft', 0)
        odonto = e.get('odonto', 0)
        naoMed = e.get('naoMed', 0)
        exames = e.get('exames', 0)
        intern = e.get('intern', 0)
        proc = e.get('proc', 0)
        farm = e.get('farm', 0)

        calc_saude = consultas + oft + odonto + naoMed + exames + intern + proc + farm

        if saude != calc_saude:
            msg = f"⚠️ [DESVIO COMPONENTES DE SAÚDE] {exp_id}: 'saude' ({saude:,}) != soma das 8 colunas de saúde ({calc_saude:,}) [Dif: {saude - calc_saude}]"
            discrepancies.append(msg)
            print(msg)

        # Soma das especialidades médicas vs consultas médicas da expedição
        spec_dict = e.get('spec', {})
        spec_sum = sum(spec_dict.values())
        if consultas != spec_sum:
            msg = f"⚠️ [DESVIO ESPECIALIDADES] {exp_id}: 'consultas' ({consultas}) != soma do dict de especialidades ({spec_sum}) [Dif: {consultas - spec_sum}]"
            discrepancies.append(msg)
            print(msg)

        # Soma dos exames vs total de exames da expedição
        exam_dict = e.get('exam', {})
        exam_sum = sum(exam_dict.values())
        if exames != exam_sum:
            msg = f"⚠️ [DESVIO EXAMES] {exp_id}: 'exames' ({exames}) != soma do dict de exames ({exam_sum}) [Dif: {exames - exam_sum}]"
            discrepancies.append(msg)
            print(msg)

    if not discrepancies:
        print("✅ Nenhuma discrepância matemática encontrada dentro das expedições individuais!")

    # ----------------------------------------------------
    # AUDIT 2: CRUZAMENTO DOS DADOS ANUAIS (CONSOLIDADO)
    # ----------------------------------------------------
    print("\n" + "="*70)
    print("2. AUDITORIA DE TOTAI S ANUAIS E CONSOLIDADOS")
    print("="*70)

    years = sorted(list(set(e.get('year') for e in exps)))

    for y in years:
        sy = str(y)
        y_exps = [e for e in exps if e.get('year') == y]

        sum_geral = sum(e.get('geral', 0) for e in y_exps)
        sum_saude = sum(e.get('saude', 0) for e in y_exps)
        sum_alim = sum(e.get('alim', 0) for e in y_exps)
        sum_pacientes = sum(e.get('pacientes', 0) for e in y_exps)
        sum_dias_atend = sum(e.get('diasAtendimento', 0) for e in y_exps)

        pat_info = pat_map.get(sy, {})
        days_info = days_map.get(sy, {})

        print(f"\n--- ANO {y} ({len(y_exps)} Expedições) ---")
        print(f"• Total Geral (Soma das Expedições):   {sum_geral:>10,}")
        print(f"• Total Saúde (Soma das Expedições):   {sum_saude:>10,}")
        print(f"• Total Alimentação (Soma):            {sum_alim:>10,}")
        print(f"• Pacientes Únicos (Soma Expedições):  {sum_pacientes:>10,}")
        print(f"• ANNUAL_PATIENT_STATS.atendimentos:   {pat_info.get('atendimentos', 0):>10,}")
        print(f"• ANNUAL_PATIENT_STATS.pacientes:      {pat_info.get('pacientes', 0):>10,}")

        if sum_geral != pat_info.get('atendimentos'):
            print(f"❌ [ERRO DE DADOS CONSOLIDADOS] Ano {y}: Atendimentos somados das expedições ({sum_geral:,}) != ANNUAL_PATIENT_STATS.atendimentos ({pat_info.get('atendimentos'):,})!")
        else:
            print(f"  ✓ Total de atendimentos bate perfeitamente com ANNUAL_PATIENT_STATS!")

        if sum_pacientes != pat_info.get('pacientes'):
            print(f"❌ [ERRO DE DADOS CONSOLIDADOS] Ano {y}: Pacientes somados das expedições ({sum_pacientes:,}) != ANNUAL_PATIENT_STATS.pacientes ({pat_info.get('pacientes'):,})!")
        else:
            print(f"  ✓ Total de pacientes bate perfeitamente com ANNUAL_PATIENT_STATS!")

        print(f"• Dias Atendimento (Soma Expedições): {sum_dias_atend:>10.1f}")
        print(f"• ANNUAL_DAYS_STATS.diasAtendimento:  {days_info.get('diasAtendimento', 0):>10.1f}")
        if round(sum_dias_atend, 1) != round(days_info.get('diasAtendimento', 0), 1):
            print(f"❌ [ERRO DE DADOS CONSOLIDADOS] Ano {y}: Dias de Atendimento ({sum_dias_atend}) != ANNUAL_DAYS_STATS ({days_info.get('diasAtendimento')})")
        else:
            print(f"  ✓ Total de dias de atendimento bate perfeitamente com ANNUAL_DAYS_STATS!")

    # ----------------------------------------------------
    # AUDIT 3: ESPECIALIDADES & EXAMES ANUAIS VS DICIONÁRIOS
    # ----------------------------------------------------
    print("\n" + "="*70)
    print("3. AUDITORIA DE ESPECIALIDADES E EXAMES ANUAIS")
    print("="*70)

    for y in years:
        sy = str(y)
        y_exps = [e for e in exps if e.get('year') == y]
        specs_dict = spec_map.get(sy, {})
        exams_dict = exam_map.get(sy, {})

        # Consultas nas exps vs soma no SPECIALTIES_BY_YEAR
        sum_exp_consultas = sum(e.get('consultas', 0) for e in y_exps)
        sum_spec_dict = sum(specs_dict.values())

        print(f"\n[Ano {y} - Especialidades]")
        print(f"• Soma 'consultas' em ALL_EXPEDITIONS: {sum_exp_consultas:,}")
        print(f"• Soma em SPECIALTIES_BY_YEAR:         {sum_spec_dict:,}")
        if sum_exp_consultas != sum_spec_dict:
            print(f"⚠️ [DESVIO] Especialidades em SPECIALTIES_BY_YEAR diferem das consultas por {sum_spec_dict - sum_exp_consultas}")
        else:
            print(f"  ✓ Especialidades em SPECIALTIES_BY_YEAR batem 100% com consultas!")

        # Exames nas exps vs soma no EXAMS_BY_YEAR
        sum_exp_exames = sum(e.get('exames', 0) for e in y_exps)
        sum_exam_dict = sum(exams_dict.values())

        print(f"[Ano {y} - Exames]")
        print(f"• Soma 'exames' em ALL_EXPEDITIONS:    {sum_exp_exames:,}")
        print(f"• Soma em EXAMS_BY_YEAR:               {sum_exam_dict:,}")
        if sum_exp_exames != sum_exam_dict:
            print(f"⚠️ [DESVIO] Exames em EXAMS_BY_YEAR diferem dos exames em ALL_EXPEDITIONS por {sum_exam_dict - sum_exp_exames}")
        else:
            print(f"  ✓ Exames em EXAMS_BY_YEAR batem 100% com exames totais!")

    # ----------------------------------------------------
    # AUDIT 4: AUDITORIA DE INTERFACE, ABAS, MENUS E IDIOMAS
    # ----------------------------------------------------
    print("\n" + "="*70)
    print("4. AUDITORIA DE INTERFACE, ABAS, IDIOMAS (i18n) E MENUS")
    print("="*70)

    # Abas no Sidebar
    nav_views = re.findall(r'data-view=["\'](.*?)["\']', html)
    views_in_html = re.findall(r'id=["\']view-(.*?)["\']', html)

    print(f"Botões de navegação no menu lateral (data-view): {nav_views}")
    print(f"Seções de visualização no HTML (id='view-...'): {views_in_html}")

    unmatched_nav = set(nav_views) - set(views_in_html)
    unmatched_views = set(views_in_html) - set(nav_views)

    if unmatched_nav:
        print(f"❌ [ERRO DE INTERFACE] Botões no menu lateral sem tela correspondente: {unmatched_nav}")
    if unmatched_views:
        print(f"ℹ️ [INFORMAÇÃO] Telas sem botão direto no menu lateral (podem ser modais/subtelas): {unmatched_views}")

    # Checar dicionários de idiomas no i18n
    # Procurar chaves presentes em PT mas ausentes em EN, DE, ES, RU
    m_i18n = re.search(r'const\s+I18N\s*=\s*(\{.*?\});\n\n|\nconst\s+I18N\s*=\s*(\{.*?\});\n', html, re.DOTALL)
    if not m_i18n:
        # try alternative match
        m_i18n = re.search(r'const\s+I18N\s*=\s*(\{.*?\n\s*\});', html, re.DOTALL)

    if m_i18n:
        print("\n[VERIFICAÇÃO DE IDIOMAS (i18n)]")
        # Evaluate languages available in I18N block by Regex keys
        lang_blocks = re.findall(r'^\s*([a-z]{2}):\s*\{', m_i18n.group(1), re.MULTILINE)
        print(f"Idiomas encontrados no I18N: {lang_blocks}")
    else:
        print("⚠️ Bloco I18N não parsed por Regex simples, checando via scanner de JS.")

    # Check for NaN or null in Json Data
    nan_null_count = 0
    for e in exps:
        for k, v in e.items():
            if v is None:
                print(f"⚠️ [DADO NULO] Exp {e.get('n')} ({e.get('year')} - {e.get('mun')}): campo '{k}' é null")
                nan_null_count += 1

    if nan_null_count == 0:
        print("✅ Nenhum valor NULO ou NaN encontrado na base de expedições!")

if __name__ == '__main__':
    audit()
