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
    "Total Dias em Atendimento": "diasAtendimento",
    "Dias em Atendimento": "diasAtendimento",
    "TOTAL DE DIAS EM ATENDIMENTO": "diasAtendimento",  # Variação com "DE" (planilha padrão)
}

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

def _dias(v):
    """Convert to float for dias (allows decimals like 4.5)"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0
    try:
        return float(v)
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
            # Use _dias for diasAtendimento to allow decimals (e.g., 4.5 days)
            if key == "diasAtendimento":
                totals[key][c] = _dias(df.iloc[r, c])
            else:
                totals[key][c] = _num(df.iloc[r, c])

    # keep only columns that actually have recorded attendance (drop future/empty placeholder columns)
    cols = [c for c in cols if totals["geral"].get(c, 0) > 0]

    municipios = {c: canonicalize_mun(_clean(df.iloc[mun_row, c])) or f"Expedição {exp_cols[c]}" for c in cols}
    datas = {c: (_clean(df.iloc[mun_row+1, c]) or "").replace("Á","à").strip() for c in cols}

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
            "diasAtendimento": totals.get("diasAtendimento", {}).get(c, 0),
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

def extract_journey_data(ods_path):
    """Extract journey metadata from 'CHEGADA E SAIDA - EXPEDICAO' sheet"""
    try:
        df = pd.read_excel(ods_path, engine="odf", sheet_name="CHEGADA E SAIDA - EXPEDICAO", header=None)
    except:
        return {}

    journey_data = {}
    municipios_data = {}

    # Header is at row 1
    header_row = 1

    for i in range(header_row + 1, len(df)):
        num_exp = df.iloc[i, 1]
        cidade = df.iloc[i, 2]
        comunidade = df.iloc[i, 3]
        saida = df.iloc[i, 4]
        chegada = df.iloc[i, 8]
        nav_ida = df.iloc[i, 6]
        nav_volta = df.iloc[i, 9]

        if pd.notna(num_exp) and "expedição" in str(num_exp).lower():
            match = re.search(r'(\d+)', str(num_exp))
            if not match:
                continue
            exp_num = int(match.group(1))

            # Calculate days
            dias_exp = 0
            if pd.notna(saida) and pd.notna(chegada):
                try:
                    saida_date = pd.to_datetime(str(saida).strip(), dayfirst=True, errors='coerce')
                    chegada_date = pd.to_datetime(str(chegada).strip(), dayfirst=True, errors='coerce')
                    if pd.notna(saida_date) and pd.notna(chegada_date):
                        dias_exp = max(0, (chegada_date - saida_date).days)
                except:
                    dias_exp = 0

            # Parse hours
            def parse_hours(h_str):
                if pd.isna(h_str):
                    return 0
                h_str = str(h_str).strip()
                try:
                    parts = h_str.split(':')
                    if len(parts) >= 2:
                        return round(int(parts[0]) + int(parts[1]) / 60, 2)
                except:
                    pass
                return 0

            horas_ida = parse_hours(nav_ida)
            horas_volta = parse_hours(nav_volta)

            journey_data[exp_num] = {
                "dias": dias_exp,
                "horas_ida": horas_ida,
                "horas_volta": horas_volta,
                "total_horas": round(horas_ida + horas_volta, 2),
                "cidade": _clean(cidade) or "-",
                "comunidade": _clean(comunidade) or "-",
            }

            # Registrar município
            mun = str(cidade).strip().title() if pd.notna(cidade) else "-"
            if mun and mun != "-":
                if mun not in municipios_data:
                    municipios_data[mun] = {
                        "comunidade": str(comunidade).strip() if pd.notna(comunidade) else "-",
                        "data_primeira": str(saida)[:10] if pd.notna(saida) else "",
                    }

    return {"journeys": journey_data, "municipios": municipios_data}

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
