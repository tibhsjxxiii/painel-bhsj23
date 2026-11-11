#!/usr/bin/env python3
"""
Script de diagnóstico para verificar a estrutura da planilha
Ajuda a identificar problemas na leitura de dados
"""
import sys
import os
import pandas as pd
import re

def diagnose_ods(ods_path):
    print(f"\n📋 DIAGNÓSTICO DA PLANILHA: {ods_path}")
    print("=" * 70)

    if not os.path.isfile(ods_path):
        print(f"❌ ERRO: Arquivo não encontrado: {ods_path}")
        return False

    print(f"✓ Arquivo encontrado: {os.path.getsize(ods_path)} bytes")

    try:
        xl = pd.ExcelFile(ods_path, engine="odf")
    except Exception as e:
        print(f"❌ ERRO ao abrir arquivo: {e}")
        return False

    print(f"\n📑 Abas encontradas ({len(xl.sheet_names)}):")
    for sheet in xl.sheet_names:
        print(f"   - {sheet}")

    # Procurar abas com anos
    year_sheets = {}
    for sheet in xl.sheet_names:
        m = re.search(r'(20\d{2})', sheet)
        if m:
            year = int(m.group(1))
            year_sheets[year] = sheet

    if not year_sheets:
        print("\n❌ ERRO: Nenhuma aba com ano foi encontrada!")
        print("   As abas precisam ter o ano no nome (ex: '2025', '2026')")
        return False

    print(f"\n✓ Abas com ano ({len(year_sheets)}):")
    for year in sorted(year_sheets.keys()):
        print(f"   - {year}: {year_sheets[year]}")

    # Analisar estrutura de cada aba
    for year in sorted(year_sheets.keys()):
        sheet_name = year_sheets[year]
        print(f"\n📊 Analisando aba {year} ({sheet_name}):")

        try:
            df = pd.read_excel(ods_path, engine="odf", sheet_name=sheet_name, header=None)
        except Exception as e:
            print(f"   ❌ Erro ao ler: {e}")
            continue

        print(f"   Dimensão: {len(df)} linhas × {df.shape[1]} colunas")

        # Procurar header (EXPEDIÇÃO)
        header_row = None
        for i in range(min(10, len(df))):
            for col in range(df.shape[1]):
                val = str(df.iloc[i, col]) if pd.notna(df.iloc[i, col]) else ""
                if "EXPEDIÇÃO" in val.upper():
                    header_row = i
                    break
            if header_row is not None:
                break

        if header_row is None:
            print(f"   ❌ ERRO: Header com 'EXPEDIÇÃO' não encontrado!")
            print(f"   Primeiras 5 linhas da coluna 0:")
            for i in range(min(5, len(df))):
                print(f"      Linha {i}: {df.iloc[i, 0]}")
            continue

        print(f"   ✓ Header encontrado na linha {header_row}")

        # Contar expedições
        exp_cols = []
        for col in range(1, df.shape[1]):
            val = str(df.iloc[header_row, col]) if pd.notna(df.iloc[header_row, col]) else ""
            if "EXPEDIÇÃO" in val.upper():
                match = re.search(r'(\d+)', val)
                if match:
                    exp_num = int(match.group(1))
                    exp_cols.append((col, exp_num))

        if not exp_cols:
            print(f"   ❌ ERRO: Nenhuma coluna com expedições encontrada!")
            print(f"   Row do header: {[df.iloc[header_row, i] for i in range(min(5, df.shape[1]))]}")
            continue

        exp_cols.sort(key=lambda x: x[1])
        print(f"   ✓ Expedições encontradas: {len(exp_cols)}")
        print(f"      Expedições: {', '.join(str(n) for _, n in exp_cols[:5])}", end="")
        if len(exp_cols) > 5:
            print(f", ... {', '.join(str(n) for _, n in exp_cols[-2:])}")
        else:
            print()

        # Procurar rótulos de dados
        labels_to_find = [
            "Total de Consultas",
            "Total de Oftalmologia",
            "Total Geral dos Atendimentos",
            "TOTAL DE DIAS EM ATENDIMENTO",
        ]

        print(f"\n   Rótulos encontrados:")
        for label in labels_to_find:
            found = False
            for i in range(len(df)):
                cell = df.iloc[i, 0]
                if pd.notna(cell) and label.lower() == str(cell).strip().lower():
                    # Pegar valor da primeira expedição
                    first_val = df.iloc[i, exp_cols[0][0]] if exp_cols else "-"
                    print(f"   ✓ {label}")
                    print(f"      Primeira exp: {first_val}")
                    found = True
                    break
            if not found:
                print(f"   ❌ {label} (NÃO ENCONTRADO)")

    # Verificar aba de jornada
    print(f"\n🗺️  Procurando aba de jornada...")
    try:
        df_journey = pd.read_excel(ods_path, engine="odf", sheet_name="CHEGADA E SAIDA - EXPEDICAO", header=None)
        print(f"   ✓ Aba 'CHEGADA E SAIDA - EXPEDICAO' encontrada")
        print(f"      Dimensão: {len(df_journey)} linhas × {df_journey.shape[1]} colunas")

        # Contar expedições na aba de jornada
        exp_count = 0
        for i in range(1, len(df_journey)):
            num_exp = df_journey.iloc[i, 1]
            if pd.notna(num_exp) and "expedição" in str(num_exp).lower():
                exp_count += 1
        print(f"      Expedições com jornada: {exp_count}")
    except:
        print(f"   ⚠️  Aba 'CHEGADA E SAIDA - EXPEDICAO' não encontrada (opcional)")

    print("\n" + "=" * 70)
    print("✅ Diagnóstico concluído!")
    return True

if __name__ == "__main__":
    # Procurar por arquivo .ods na pasta
    ods_file = None
    for f in os.listdir("."):
        if f.endswith(".ods"):
            ods_file = f
            break

    if not ods_file:
        print("❌ Nenhum arquivo .ods encontrado na pasta atual!")
        print("Coloque a planilha nesta pasta e tente novamente.")
        sys.exit(1)

    diagnose_ods(ods_file)
