# DISC Assessment Bank Import Guide

This guide explains how to populate the DISC assessment database with question banks, scenarios, and configuration data.

## Overview

The DISC import system supports:
- **12 data types**: Normative items, ipsative blocks, scenarios, Likert mapping, scoring rules, thresholds, report templates, descriptive words, interview guides, quality checks, and ethics
- **Bilingual support**: PT (Portuguese) and EN (English) with automatic translation
- **Version tracking**: Multiple assessment versions with full history
- **Idempotent imports**: Safe to run multiple times without duplicates

## Database Schema

The system creates 12 specialized tables in Supabase:
- `disc_versions` - Version tracking
- `disc_items_norm` - 120 normative assessment items
- `disc_blocks_ipsa` - 24 ipsative (forced-choice) blocks
- `disc_scenarios` - 12 situational judgment scenarios
- `disc_likert_map` - 5-point Likert scale mapping
- `disc_rules` - Scoring calculation rules
- `disc_thresholds` - Interpretation thresholds (D, I, S, C)
- `disc_report_templates` - Report section templates
- `disc_words` - Descriptive words by factor/intensity
- `disc_interview` - Interview guide questions
- `disc_quality_checks` - Quality validation criteria
- `disc_ethics` - Ethical principles

## Migration

Run the database migration to create the schema:

```bash
# The migration is already in the supabase/migrations folder
# It will be applied automatically when you deploy or run migrations
```

## Excel File Structure

The import system expects an Excel file with 12 sheets:

1. **Itens_Normativos** (120 rows) - Normative items with:
   - item_id, texto_pt, texto_simples_pt, fator_primario
   - peso_d, peso_i, peso_s, peso_c (factor weights)
   - invertido, sutil, contexto, leitura_nivel

2. **Blocos_Ipsativos** (24 rows) - Ipsative blocks with:
   - bloco_id
   - frase_a_pt, fator_a, frase_b_pt, fator_b, frase_c_pt, fator_c, frase_d_pt, fator_d

3. **Cenarios** (12 rows) - Scenarios with:
   - cenario_id, prompt_pt
   - opc_a_pt, fator_a, opc_b_pt, fator_b, opc_c_pt, fator_c, opc_d_pt, fator_d

4. **Likert_Mapa** (5 rows) - Likert mapping with:
   - resposta (1-5), ancora_pt
   - escore_d, escore_i, escore_s, escore_c, escore_im

5. **Regras_Score** - Scoring rules with:
   - regra_id, descricao_pt, formula_pt, aplicacao

6. **Normas_Thresholds** (4 rows) - Thresholds with:
   - fator (D/I/S/C), baixo, medio, alto, nota_pt

7. **Relatorio_Templates** - Report templates with:
   - secao_key, secao_pt, condicao, texto_pt, bullets_pt, metricas, placeholders

8. **Palavras_Descritivas** (12 rows) - Words with:
   - fator (D/I/S/C), intensidade (baixa/média/alta), lista_pt

9. **Guia_Entrevista** - Interview questions with:
   - eixo (D/I/S/C), pergunta_pt, observar_pt, follow_pt

10. **Validacao_Qualidade** - Quality checks with:
    - checagem_pt, criterio_pt, acao_pt

11. **Manifesto_Ético** - Ethics with:
    - principio_pt, como_aplicamos_pt

12. **Versao** (1 row) - Version metadata with:
    - version, data_criacao, notes

## Import Command

Use the Django management command to import data:

```bash
# Basic import (auto-detect version)
python app/manage.py import_disc path/to/DISC_QuestionBank.xlsx

# Specify version explicitly
python app/manage.py import_disc path/to/DISC_QuestionBank.xlsx --version "1.0"

# Skip automatic translation
python app/manage.py import_disc path/to/DISC_QuestionBank.xlsx --no-translate
```

### Expected Output

```
============================================================
DISC Assessment Bank Importer
============================================================
File: DISC_QuestionBank.xlsx
Version: Auto-detect
Translation: Enabled

Starting import...

✓ Import successful!

Version: 1.0
Version ID: abc123...

Record counts:
  norm                : 120 records
  ipsa                : 24 records
  scenarios           : 12 records
  likert              : 5 records
  rules               : 10 records
  thresholds          : 4 records
  templates           : 22 records
  words               : 12 records
  interview           : 16 records
  quality             : 8 records
  ethics              : 6 records
  TOTAL               : 239 records

============================================================
```

## API Endpoints

### Query Question Bank

```http
GET /api/disc/bank?version=1.0&lang=pt&type=norm&page=1&pageSize=50
```

Parameters:
- `version` - Version string (default: latest)
- `lang` - Language: 'pt' or 'en' (default: 'pt')
- `type` - Item type: 'norm', 'ipsa', or 'scen' (default: 'norm')
- `page` - Page number (default: 1)
- `pageSize` - Items per page (default: 50, max: 200)

Response:
```json
{
  "version": "1.0",
  "lang": "pt",
  "type": "norm",
  "page": 1,
  "pageSize": 50,
  "items": [
    {
      "item_id": "DISC001",
      "texto": "Eu sou uma pessoa decisiva",
      "texto_simples": "Sou decisivo",
      "fator_primario": "D",
      "peso_d": 1.0,
      "peso_i": 0.0,
      "peso_s": 0.0,
      "peso_c": 0.0,
      "invertido": false
    }
  ],
  "hasMore": true
}
```

### Get Templates and Configuration

```http
GET /api/disc/templates?version=1.0&lang=pt
```

Parameters:
- `version` - Version string (default: latest)
- `lang` - Language: 'pt' or 'en' (default: 'pt')

Response:
```json
{
  "version": "1.0",
  "lang": "pt",
  "data": {
    "report_templates": [...],
    "thresholds": [...],
    "likert_map": [...],
    "words": [...],
    "interview": [...],
    "quality_checks": [...],
    "ethics": [...],
    "rules": [...]
  }
}
```

## Translation

The system automatically translates missing English fields from Portuguese:

1. **Placeholder Preservation**: Maintains `{NOME}`, `{CARGO}`, `{DATA}`, `{D_final}`, etc.
2. **Factor Codes**: Preserves D, I, S, C letter codes
3. **IDs**: Never translates item_id, bloco_id, cenario_id
4. **Style**: Corporate-friendly, inclusive, 6th-8th grade reading level

## Idempotent Imports

The system uses natural keys (item_id, bloco_id, cenario_id) for upserts:
- Running import twice with same file updates existing records
- No duplicates created
- Safe to re-import after Excel updates

## Validation

The import validates:
- All 12 required sheets present
- Minimum row counts (120 items, 24 blocks, 12 scenarios, 5 Likert, 4 thresholds)
- Required fields populated
- Valid factor codes (D, I, S, C)
- Numeric ranges for weights and scores

## Security

- RLS enabled on all tables
- Authenticated users can read all DISC data
- Only SUPER_ADMIN and ORG_ADMIN can import/update data
- Version-scoped queries prevent data leakage

## Troubleshooting

### Import Fails - Missing Sheets
```
Error: Missing required sheet: Itens_Normativos
```
**Solution**: Ensure Excel file has all 12 sheets with exact names

### Import Fails - Row Count
```
Error: Sheet 'Itens_Normativos' has 80 rows, expected at least 120
```
**Solution**: Add missing rows to meet minimum requirements

### Translation Not Working
```
Warning: Translation failed: ...
```
**Solution**: System falls back to simple word replacement. Check LLM client configuration.

### API Returns Empty
```
{"error": "No DISC data available"}
```
**Solution**: Run import command first to populate database

## Files Created

- `supabase/migrations/20251010020000_create_disc_assessment_bank.sql` - Database schema
- `app/assessments/disc_importer.py` - Import logic
- `app/assessments/disc_translator.py` - Translation service
- `app/assessments/disc_api.py` - API endpoints
- `app/assessments/management/commands/import_disc.py` - Django command

## Next Steps

1. Run the migration to create database schema
2. Prepare Excel file with DISC data
3. Run import command: `python app/manage.py import_disc DISC_QuestionBank.xlsx`
4. Test API endpoints to verify data access
5. Build frontend components to consume DISC data

## Support

For issues or questions, check:
- Django logs for import errors
- Supabase dashboard for data verification
- API responses for data structure
