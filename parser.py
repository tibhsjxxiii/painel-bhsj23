import pandas as pd
import re

TOTAL_LABELS = {
    "Total de Consultas": "consultas",
    "Total de Oftalmologia": "oft",
    "Total de Odontologia": "odonto",
    "Total de Consultas Não Médicas": "naoMed",
    "Total de Exames": "exames",
    "Total de Internações e Procedimentos": "intern",
    "Total de Procedimentos": "proc",
    "Total de Farmácia": "farm",
    "Entrega de Alimentação": "alim",
    "Total de Atendimentos em Saúde": "saude",
    "Total Geral dos Atendimentos": "geral",
}

# Dias em atendimento (extracted separately)
DAYS_LABEL = "Total de Dias em Atendimento"

CANONICAL_MUN = {
    "ANAMA": "Anamã", "ANAMÃ": "Anamã",
    "URUCARA": "Urucará", "URUCARÁ": "Urucará",
    "BERURI": "Beruri", "BERURI II": "Beruri",
    "NOVO AIRÂO": "Novo Airão", "NOVO AIRÃO": "Novo Airão",
    "NOVO REMANÇO I": "Novo Remanso I", "NOVO REMANSO I": "Novo Remanso I",
    "NOVO REMANÇO II": "Novo Remanso II", "NOVO REMANSO II": "Novo Remanso II",
    "CODAJAS": "Codajás", "CODAJÁS": "Codajás",
    "BELEM": "Belém", "BELÉM": "Belém",
    "CAREIRO DA VARZEA": "Careiro da Várzea", "CAREIRO DA VÁRZEA": "Careiro da Várzea",
    "NHAMUNDA": "Nhamundá", "NHAMUNDÁ": "Nhamundá",
}

def canonicalize_mun(raw):
    if not raw:
        return raw
    key = raw.strip().upper()
    if key in CANONICAL_MUN:
        return CANONICAL_MUN[key]
    return raw.strip().title()

def _clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None

def _num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0
    try:
        return int(round(float(v)))
    except (ValueError, TypeError):
        return 0

def find_expedition_columns(df):
    """Find the header row listing '<n> EXPEDIÇÃO' and return {col_index: expedition_label}."""
    for i in range(min(6, len(df))):
        row = df.iloc[i, :]
        matches = {}
        for col in range(1, df.shape[1]):
            val = _clean(row[col])
            if val and re.search(r'EXPEDI[ÇC][ÃA]O', val, re.IGNORECASE):
                m = re.match(r'\s*(\S+)\s*EXPEDI', val, re.IGNORECASE)
                label = m.group(1) if m else str(col)
                matches[col] = label
        if len(matches) >= 2:
            return i, matches
    return None, {}

def find_row_by_label(df, label, col=0):
    for i in range(len(df)):
        val = _clean(df.iloc[i, col])
        if val and val.strip().lower() == label.strip().lower():
            return i
    return None

def parse_year_sheet(df, year):
    header_row, exp_cols = find_expedition_columns(df)
    if not exp_cols:
        return None
    cols = sorted(exp_cols.keys())
    mun_row = header_row + 1

    def expedition_number(label, col):
        m = re.match(r'^\d+$', label)
        return int(label) if m else label

    # totals (compute first so we can drop placeholder/empty future-expedition columns)
    totals = {key: {} for key in TOTAL_LABELS.values()}
    for label, key in TOTAL_LABELS.items():
        r = find_row_by_label(df, label)
        if r is None:
            continue
        for c in cols:
            totals[key][c] = _num(df.iloc[r, c])

    # keep only columns that actually have recorded attendance (drop future/empty placeholder columns)
    cols = [c for c in cols if totals["geral"].get(c, 0) > 0]

    municipios = {c: canonicalize_mun(_clean(df.iloc[mun_row, c])) or f"Expedição {exp_cols[c]}" for c in cols}
    datas = {c: (_clean(df.iloc[mun_row+1, c]) or "").replace("Á","à").strip() for c in cols}

    # Extract "Total de Dias em Atendimento" for each expedition
    dias_atendimento = {}
    r_dias = find_row_by_label(df, DAYS_LABEL)
    if r_dias is not None:
        for c in cols:
            val = df.iloc[r_dias, c]
            # Handle NaN/None/empty values FIRST
            if val is None or (isinstance(val, float) and pd.isna(val)):
                dias_atendimento[c] = 0
            elif isinstance(val, str):
                # Try to parse "5,5" or "4.5" formats
                val = val.strip().replace(",", ".")
                try:
                    dias_atendimento[c] = float(val) if val else 0
                except (ValueError, TypeError):
                    dias_atendimento[c] = 0
            else:
                try:
                    dias_atendimento[c] = float(val) if val else 0
                except (ValueError, TypeError):
                    dias_atendimento[c] = 0
    else:
        # Default to 0 if row not found
        dias_atendimento = {c: 0 for c in cols}

    # specialties: rows strictly between "Consultas Médicas" and "Total de Consultas"
    specialties = {}
    specialties_per_col = {c: {} for c in cols}
    r_spec_start = find_row_by_label(df, "Consultas Médicas")
    r_spec_end = find_row_by_label(df, "Total de Consultas")
    if r_spec_start is not None and r_spec_end is not None and r_spec_end > r_spec_start:
        for i in range(r_spec_start + 1, r_spec_end):
            label = _clean(df.iloc[i, 0])
            if not label:
                continue
            val = sum(_num(df.iloc[i, c]) for c in cols)
            specialties[label] = specialties.get(label, 0) + val
            for c in cols:
                v = _num(df.iloc[i, c])
                if v:
                    specialties_per_col[c][label] = specialties_per_col[c].get(label, 0) + v

    # exams: rows strictly between "Exames" (section header) and the next TOTAL_LABEL row after it
    exams = {}
    exams_per_col = {c: {} for c in cols}
    r_exam_start = find_row_by_label(df, "Exames")
    if r_exam_start is not None:
        r_exam_end = None
        for i in range(r_exam_start + 1, len(df)):
            label = _clean(df.iloc[i, 0])
            if label and label.strip() in TOTAL_LABELS:
                r_exam_end = i
                break
        if r_exam_end is None:
            r_exam_end = min(r_exam_start + 12, len(df))
        for i in range(r_exam_start + 1, r_exam_end):
            label = _clean(df.iloc[i, 0])
            if not label:
                continue
            val = sum(_num(df.iloc[i, c]) for c in cols)
            exams[label] = exams.get(label, 0) + val
            for c in cols:
                v = _num(df.iloc[i, c])
                if v:
                    exams_per_col[c][label] = exams_per_col[c].get(label, 0) + v

    # detailed breakdown rows (small/medium surgery, dental procedures vs consultations)
    DETAIL_LABELS = {
        "Cirurgias de Baixa Complexidade": "cirBaixa",
        "Cirurgias de Média Complexidade": "cirMedia",
        "Procedimentos Odontológicos": "procOdonto",
        "Consulta Odontológica": "consultaOdonto",
        "Internações Clinicas/ Cirurgicas": "internClinCir",
        "Total de Pacientes Atendidos": "pacientes",
    }
    detail_totals = {key: {} for key in DETAIL_LABELS.values()}
    for label, key in DETAIL_LABELS.items():
        r = find_row_by_label(df, label)
        if r is None:
            continue
        for c in cols:
            detail_totals[key][c] = _num(df.iloc[r, c])

    expeditions = []
    for c in cols:
        expeditions.append({
            "year": year,
            "n": expedition_number(exp_cols[c], c),
            "mun": municipios[c],
            "data": datas[c],
            "diasAtendimento": dias_atendimento.get(c, 0),
            "diasExpedicao": 7,  # Padrão de 7 dias por expedição
            "consultas": totals["consultas"].get(c, 0),
            "oft": totals["oft"].get(c, 0),
            "odonto": totals["odonto"].get(c, 0),
            "naoMed": totals["naoMed"].get(c, 0),
            "exames": totals["exames"].get(c, 0),
            "intern": totals["intern"].get(c, 0),
            "proc": totals["proc"].get(c, 0),
            "farm": totals["farm"].get(c, 0),
            "alim": totals["alim"].get(c, 0),
            "saude": totals["saude"].get(c, 0),
            "geral": totals["geral"].get(c, 0),
            "cirBaixa": detail_totals["cirBaixa"].get(c, 0),
            "cirMedia": detail_totals["cirMedia"].get(c, 0),
            "procOdonto": detail_totals["procOdonto"].get(c, 0),
            "consultaOdonto": detail_totals["consultaOdonto"].get(c, 0),
            "internClinCir": detail_totals["internClinCir"].get(c, 0),
            "pacientes": detail_totals["pacientes"].get(c, 0),
            "spec": specialties_per_col[c],
            "exam": exams_per_col[c],
        })

    return {"expeditions": expeditions, "specialties": specialties, "exams": exams}

def time_to_minutes(time_str):
    """Converte formato HH:MM ou H:MM para minutos totais."""
    if not time_str or (isinstance(time_str, float) and pd.isna(time_str)):
        return 0
    time_str = str(time_str).strip()
    if not time_str or time_str == "-":
        return 0
    try:
        parts = time_str.split(":")
        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
    except:
        pass
    return 0

def extract_navigation_data(ods_path):
    """Extrai dados de navegação da aba 'CHEGADA E SAIDA - EXPEDICAO'."""
    navigation = {}
    try:
        df = pd.read_excel(ods_path, engine="odf", sheet_name="CHEGADA E SAIDA - EXPEDICAO", header=None)

        # Pular header (linha 0)
        for idx in range(1, len(df)):
            row = df.iloc[idx]
            ano = row[0]
            num_exp = row[1]
            comunidade = row[3]
            nav_ida = row[6]  # Navegação Ida
            nav_volta = row[9]  # Navegação Volta

            # Validar ano (deve ser número)
            if not ano or (isinstance(ano, float) and pd.isna(ano)):
                continue
            try:
                ano = int(float(ano))
            except:
                continue

            if 2020 <= ano <= 2030:
                # Extrair número da expedição (ex: "2ª Expedição" -> 2)
                try:
                    num_match = re.search(r'(\d+)', str(num_exp))
                    if num_match:
                        num = int(num_match.group(1))
                    else:
                        continue
                except:
                    continue

                key = f"{ano}_{num}"
                ida_min = time_to_minutes(nav_ida)
                volta_min = time_to_minutes(nav_volta)

                navigation[key] = {
                    "comunidade": _clean(comunidade),
                    "idaMin": ida_min,
                    "voltaMin": volta_min,
                }

    except Exception as e:
        print(f"⚠️  Aviso: não foi possível ler aba de navegação: {e}")

    return navigation

def extract_all_years(ods_path):
    xl = pd.ExcelFile(ods_path, engine="odf")
    result = {}
    for sheet_name in xl.sheet_names:
        m = re.search(r'(20\d{2})', sheet_name)
        if not m:
            continue
        year = int(m.group(1))
        df = pd.read_excel(ods_path, engine="odf", sheet_name=sheet_name, header=None)
        parsed = parse_year_sheet(df, year)
        if parsed and parsed["expeditions"]:
            result[year] = parsed
    return result
