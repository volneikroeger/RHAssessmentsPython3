# Psychological Assessments SaaS Platform

A comprehensive multi-tenant SaaS platform for psychological assessments and Individual Development Plan (PDI) management, built with Django 5.x, PostgreSQL with Row Level Security, and modern web technologies.

## 🏗️ Architecture Overview

### Technology Stack
- **Backend**: Django 5.x with PostgreSQL 16
- **Frontend**: Django Templates + htmx + Alpine.js
- **Charts**: Chart.js for radar and bar charts
- **Cache/Queue**: Redis 7 + Celery 5
- **Authentication**: django-allauth (Google + Microsoft OAuth)
- **Security**: CSP, Rate limiting, PII encryption (Fernet), Row Level Security
- **Exports**: WeasyPrint (PDF), pandas + XlsxWriter (CSV/XLSX)
- **Storage**: django-storages with S3 compatibility
- **Packaging**: Poetry with locked dependencies
- **Testing**: pytest, factory_boy, playwright
- **DevX**: Docker Compose, pre-commit hooks, Makefile

### Key Features

#### Multi-Tenancy
- **Strong tenant isolation** with PostgreSQL Row Level Security (RLS)
- Tenant resolution by subdomain, header, or path prefix
- Thread-local tenant context with automatic filtering
- Comprehensive audit logging

#### Two Business Models
1. **Companies (HR + PDI)**: Employee assessments, automatic PDI generation, managerial approval workflows
2. **Recruiters (R&S)**: Candidate assessments, job matching, client reporting, ranking systems

#### Assessment Engine
- **Configurable frameworks**: Big Five (IPIP), DISC, Career Anchors, OCEAN
- **Multiple question types**: Likert scales, forced choice, ipsative ranking, matrix
- **Scoring algorithms**: Dimensional scoring, percentiles, norm tables
- **Automated reporting**: HTML + PDF with charts and interpretations
- **Multilingual support**: PT-BR/EN with localized content

#### PDI (Individual Development Plans)
- **Auto-generation** from assessment profiles
- **SMART goals** with metrics, deadlines, and ownership
- **Approval workflows** for managers and HR
- **Progress tracking** with status updates and reminders
- **Action catalog** with pre-defined development activities

#### Billing & Subscriptions
- **Configurable plans** with usage limits (assessments/month, team members, modules)
- **PayPal** (primary) and **Stripe** (secondary) integration
- **Webhook handling** for renewals and dunning
- **Usage metering** with graceful blocking when limits exceeded
- **Super admin panel** for tenant and billing management

#### LGPD/Privacy Compliance
- **Consent management** with versioned terms and policies
- **Data Subject Rights** (DSR): export and deletion workflows
- **PII encryption** using Fernet fields
- **Data retention** policies with automated cleanup
- **Audit trails** for all data access and modifications

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (for local development)
- Poetry (for dependency management)

### Running with Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd psychological-assessments-saas

# Copy environment variables
cp .env.example .env

# Start all services
make dev

# The application will be available at:
# http://localhost:8000
```

The `make dev` command will:
1. Build Docker images
2. Start PostgreSQL, Redis, Django web server, Celery worker, and Celery beat
3. Run database migrations (including RLS setup)
4. Load seed data with sample organizations and assessments
5. Create a super admin user

### Local Development (Without Docker)

```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env

# Start PostgreSQL and Redis services locally
# Update DATABASE_URL and REDIS_URL in .env accordingly

# Run migrations and seed data
make local-migrate
make local-seed

# Start development server
make local-dev
```

## 🗄️ Database Schema

### Core Entities

#### Organizations
- Multi-tenant root entity with `COMPANY` or `RECRUITER` types
- Subdomain-based routing support
- Localization and branding settings

#### Users & Memberships
- Custom email-based User model with encrypted PII
- Role-based membership system (SUPER_ADMIN, ORG_ADMIN, MANAGER, HR, RECRUITER, MEMBER, VIEWER)
- Invitation workflows with secure tokens

#### Assessments
- **AssessmentDefinition**: Framework specifications (Big Five, DISC, etc.)
- **AssessmentInstance**: Individual assessment sessions with tokens
- **Session/Response**: User interaction and answer storage
- **ScoreProfile**: Calculated dimensional scores and percentiles
- **Report**: Generated HTML and PDF reports

#### PDI System
- **PDIPlan**: Development plan linked to assessment results
- **PDITask**: Individual SMART goals with tracking

#### Billing
- **Plan**: Configurable subscription tiers with limits
- **Subscription**: Active subscriptions with provider integration
- **UsageMeter**: Real-time usage tracking per billing cycle

### Row Level Security (RLS)

All tenant-scoped tables use PostgreSQL RLS with policies:

```sql
-- Example RLS policy
CREATE POLICY tenant_iso_select ON public.assessments_instance
FOR SELECT USING (organization_id::text = current_setting('app.current_tenant', true));

CREATE POLICY tenant_iso_write ON public.assessments_instance
FOR ALL USING (organization_id::text = current_setting('app.current_tenant', true))
WITH CHECK (organization_id::text = current_setting('app.current_tenant', true));
```

## 🧪 Assessment Instruments

The platform includes several psychological assessment tools:

### Big Five Personality (IPIP-50)
- **Public domain** 50-item questionnaire
- Measures: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- Available in PT-BR and EN
- Includes percentile norms and interpretive text

### DISC Assessment
- **Proprietary implementation** with ipsative and normative versions
- Measures: Dominance, Influence, Steadiness, Conscientiousness
- Forced-choice pairs and Likert scale variants
- Comparative scoring and behavioral insights

### Career Anchors
- **Inspired by Schein's model** with original items
- 8 career orientations: Technical, Managerial, Autonomy, Security, etc.
- Career guidance and development planning integration

### Custom Instruments
The platform supports creating new assessment instruments via JSON configuration files in `/app/seeds/instruments/`.

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/assessments_db

# Security
SECRET_KEY=your-secret-key
PII_ENCRYPTION_KEY=your-fernet-key

# OAuth (optional)
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH_GOOGLE_SECRET=your-google-secret
OAUTH_MICROSOFT_CLIENT_ID=your-microsoft-client-id
OAUTH_MICROSOFT_SECRET=your-microsoft-secret

# Payment Processing (optional)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-secret
STRIPE_SECRET_KEY=your-stripe-secret
```

### Feature Flags

Control platform features via environment variables:
- `ENABLE_REGISTRATION=True` - Allow new user registration
- `ENABLE_BILLING=True` - Enable subscription management
- `ENABLE_ANALYTICS=True` - Track usage metrics

## 🧪 Testing

### Running Tests

```bash
# Full test suite
make test

# With coverage report
make test-coverage

# Specific test categories
pytest app/tests/unit/          # Unit tests
pytest app/tests/integration/   # Integration tests
pytest app/tests/e2e/          # End-to-end tests
```

### Test Strategy

- **Unit Tests**: Assessment scoring, PDI generation, billing calculations
- **Integration Tests**: Multi-tenant data isolation, complete user workflows
- **E2E Tests**: Browser automation with Playwright (login → assessment → report → PDI)
- **Security Tests**: RLS verification, permission boundary testing

## 📊 Monitoring & Observability

### Logging
- Structured JSON logging for production
- Request/response tracking with correlation IDs
- Security event logging (failed logins, permission violations)

### Health Checks
- `/health/` endpoint for container orchestration
- Database connectivity checks
- Redis availability verification

### Metrics
- Celery task monitoring
- Assessment completion rates
- Subscription renewal tracking
- API response time monitoring

## 🔒 Security Features

### Data Protection
- **PII Encryption**: Sensitive fields encrypted at rest using Fernet
- **Row Level Security**: Database-level tenant isolation
- **CSP Headers**: Content Security Policy preventing XSS
- **Rate Limiting**: Login and API endpoint protection

### Compliance
- **LGPD/GDPR Ready**: Data export/deletion workflows
- **Audit Logging**: Complete action tracking
- **Consent Management**: Versioned terms and privacy policies
- **Data Retention**: Configurable cleanup policies

## 🌐 Internationalization

### Supported Languages
- **English (en)**: Default language
- **Portuguese Brazil (pt-br)**: Complete translation including assessment content

### Adding New Languages

1. Add language to `LANGUAGES` in `settings.py`
2. Create translation files: `python manage.py makemessages -l <lang_code>`
3. Translate assessment instruments in `/app/seeds/instruments/`
4. Update templates and forms

## 💳 Billing Integration

### PayPal Integration (Primary)
- Subscription creation and management
- Webhook handling for payment events
- Automatic plan upgrades/downgrades

### Stripe Integration (Secondary)
- Alternative payment processor
- Identical feature parity with PayPal
- Webhook signature verification

### Usage Metering
- Real-time assessment usage tracking
- Monthly/annual billing cycle support
- Soft limits with graceful degradation
- Overage billing for enterprise plans

## 🚀 Deployment

### Production Checklist

1. **Environment**: Set `DEBUG=False`, configure secure `SECRET_KEY`
2. **Database**: Use managed PostgreSQL with SSL
3. **Storage**: Configure S3-compatible storage for media files
4. **Email**: Set up transactional email service (SES/SendGrid)
5. **SSL**: Enable HTTPS with proper certificates
6. **Monitoring**: Configure Sentry for error tracking

### Docker Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    build: .
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://...
    deploy:
      replicas: 3
```

## 📖 API Documentation

### Webhook Endpoints

#### PayPal Webhooks
- `POST /api/webhooks/paypal/` - Handle subscription events
- Verifies webhook signature
- Processes subscription updates, cancellations, and payment failures

#### Stripe Webhooks  
- `POST /api/webhooks/stripe/` - Handle payment events
- Signature verification using webhook secret
- Idempotent event processing

## 🤝 Contributing

### Development Workflow

1. **Setup**: Fork repository and create feature branch
2. **Code**: Follow PEP 8 and Django best practices
3. **Test**: Ensure all tests pass and add new test coverage
4. **Lint**: Run `make lint` and `make fmt` before committing
5. **Review**: Submit PR with clear description and test evidence

### Code Quality Tools

- **Ruff**: Fast Python linter and formatter
- **mypy**: Static type checking
- **pre-commit**: Automated code quality checks
- **pytest**: Testing framework with fixtures and factories

## ⚠️ Important Disclaimers

### Professional Use Only
This platform is designed for **organizational and educational use only**. It is:
- ✅ Suitable for HR assessments and team development
- ✅ Appropriate for recruitment screening and candidate evaluation
- ✅ Useful for leadership development and training programs
- ❌ **NOT for clinical diagnosis or therapeutic intervention**
- ❌ **NOT a substitute for licensed psychological services**
- ❌ **NOT validated for medical or psychiatric purposes**

### Regulatory Compliance
- **CFP (Brazil)**: Complies with Brazilian Psychology Council guidelines for non-clinical use
- **SatePsi**: Assessment content follows psychological testing standards where applicable
- **LGPD/GDPR**: Full data protection compliance with consent management
- **ISO 27001**: Security practices aligned with information security standards

### Liability Limitations
Users and organizations are responsible for:
- Appropriate use within their legal jurisdiction
- Compliance with local privacy and employment laws  
- Proper interpretation of assessment results
- Ethical application of psychological insights

## 📞 Support & Documentation

### Getting Help
- **Documentation**: Complete API and user guides in `/docs/`
- **Community**: GitHub Discussions for questions and feature requests
- **Issues**: Bug reports and enhancement requests via GitHub Issues
- **Enterprise**: Professional support and customization available

### Version Compatibility
- **Python**: 3.12+ required
- **Django**: 5.x series supported
- **PostgreSQL**: 14+ recommended, 16+ for optimal RLS performance
- **Node.js**: Not required (frontend uses CDN libraries)

---

**Built with ❤️ for the psychological assessment and HR development community.**

*Last updated: December 2024*