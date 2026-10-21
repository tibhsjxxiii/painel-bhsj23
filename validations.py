#!/usr/bin/env python3
"""
Módulo de Validação de Expedições
==================================
Valida integridade e consistência dos dados de expedições.
"""

class ValidationReport:
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def add_error(self, category, message):
        self.errors.append({
            'category': category,
            'message': message
        })
    
    def add_warning(self, category, message):
        self.warnings.append({
            'category': category,
            'message': message
        })
    
    def get_summary(self):
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings)
        }


def validate_all_expeditions(all_expeditions):
    """
    Valida todos os dados de expedições.
    """
    report = ValidationReport()
    
    if not all_expeditions:
        report.add_error('DATA', 'Nenhuma expedição encontrada')
        return report
    
    # Verificar campos obrigatórios
    for exp in all_expeditions:
        if not exp.get('n'):
            report.add_warning('EXPEDICION', f'Expedição sem número identificador')
        
        if not exp.get('mun') or exp['mun'].strip() == '':
            report.add_warning('MUNICIPIO', f'Expedição {exp.get("n", "?")} sem município')
        
        if exp.get('geral', 0) == 0:
            report.add_warning('ATENDIMENTO', f'Expedição {exp.get("n", "?")} com atendimento zero')
    
    # Verificar navegação
    for exp in all_expeditions:
        if exp.get('horarios'):
            nav = exp['horarios']
            
            # Validar navegação_ida
            if nav.get('navegacao_ida'):
                ida_str = str(nav['navegacao_ida'])
                if ':' in ida_str:
                    try:
                        partes = ida_str.split(':')
                        if len(partes) >= 2:
                            horas = int(partes[0])
                            minutos = int(partes[1])
                            if minutos >= 60:
                                report.add_warning('NAVEGACAO', 
                                    f'Expedição {exp.get("n")} - Minutos inválidos em navegação_ida: {ida_str}')
                    except (ValueError, IndexError):
                        pass
    
    return report
