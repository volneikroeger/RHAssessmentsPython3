# DISC Assessment Bank - Quick Start

## 🚀 In 3 Steps

### 1. Run Migration
```bash
# Migration is at: supabase/migrations/20251010020000_create_disc_assessment_bank.sql
# Will be applied automatically on deployment
```

### 2. Import Data
```bash
python app/manage.py import_disc DISC_QuestionBank.xlsx
```

### 3. Access via API
```bash
# Get questions
curl "http://localhost:8000/api/disc/bank?lang=pt&type=norm"

# Get templates
curl "http://localhost:8000/api/disc/templates?lang=en"
```

## 📋 Excel File Requirements

Your Excel file must have 12 sheets:

| Sheet Name | Min Rows | Contains |
|------------|----------|----------|
| Itens_Normativos | 120 | Assessment items |
| Blocos_Ipsativos | 24 | Forced-choice blocks |
| Cenarios | 12 | Situational scenarios |
| Likert_Mapa | 5 | Scale mapping |
| Regras_Score | 1+ | Scoring rules |
| Normas_Thresholds | 4 | Factor thresholds |
| Relatorio_Templates | 1+ | Report templates |
| Palavras_Descritivas | 12 | Descriptive words |
| Guia_Entrevista | 1+ | Interview questions |
| Validacao_Qualidade | 1+ | Quality checks |
| Manifesto_Ético | 1+ | Ethics principles |
| Versao | 1 | Version metadata |

## 📌 Key Commands

```bash
# Basic import
python app/manage.py import_disc file.xlsx

# Specify version
python app/manage.py import_disc file.xlsx --version "2.0"

# Skip translation
python app/manage.py import_disc file.xlsx --no-translate
```

## 🔌 API Endpoints

### GET `/api/disc/bank`
```
?version=1.0    # Version (default: latest)
&lang=pt        # Language: pt or en (default: pt)
&type=norm      # Type: norm, ipsa, scen (default: norm)
&page=1         # Page number
&pageSize=50    # Items per page (max 200)
```

### GET `/api/disc/templates`
```
?version=1.0    # Version (default: latest)
&lang=pt        # Language: pt or en (default: pt)
```

## 💡 Pro Tips

1. **Idempotent**: Safe to run import multiple times
2. **Translation**: Empty EN fields auto-translated from PT
3. **Placeholders**: `{NOME}`, `{CARGO}`, etc. preserved in translation
4. **Versions**: Multiple versions supported, query by version number
5. **Security**: Authenticated users can read, admins can import

## 🔧 Dependencies

Add to your environment:
```bash
poetry add openpyxl supabase
# or
pip install openpyxl supabase
```

## 📖 Full Documentation

- `DISC_IMPORT_GUIDE.md` - Complete guide
- `DISC_IMPLEMENTATION_SUMMARY.md` - Technical details

## ✅ Success Output

```
============================================================
DISC Assessment Bank Importer
============================================================
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

## 🆘 Troubleshooting

| Error | Solution |
|-------|----------|
| Missing sheet | Check Excel has all 12 sheets with exact names |
| Row count low | Add missing rows to meet minimums |
| Translation fails | System uses fallback, or disable with `--no-translate` |
| API empty | Run import command first |

## 📞 Files Created

- Database: `supabase/migrations/20251010020000_create_disc_assessment_bank.sql`
- Import: `app/assessments/disc_importer.py`
- Translation: `app/assessments/disc_translator.py`
- API: `app/assessments/disc_api.py`
- Command: `app/assessments/management/commands/import_disc.py`
