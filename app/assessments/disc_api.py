"""
DISC Assessment Bank API Views

Provides read-only API endpoints for accessing DISC assessment data:
- /api/disc/bank - Paginated question bank queries
- /api/disc/templates - Report templates and configuration data
"""
import json
import logging
from typing import Dict, List, Any, Optional
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    supabase_url = config('VITE_SUPABASE_URL', default=config('SUPABASE_URL', default=''))
    supabase_key = config('VITE_SUPABASE_ANON_KEY', default=config('SUPABASE_KEY', default=''))

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured")

    return create_client(supabase_url, supabase_key)


class DISCBankView(LoginRequiredMixin, View):
    """
    GET /api/disc/bank

    Query parameters:
        - version: Version string (default: latest)
        - lang: Language code 'pt' or 'en' (default: 'pt')
        - type: Data type - 'norm', 'ipsa', 'scen' (default: 'norm')
        - page: Page number (default: 1)
        - pageSize: Items per page (default: 50, max: 200)

    Returns paginated DISC assessment items in requested language.
    """

    def get(self, request):
        try:
            # Parse query parameters
            version = request.GET.get('version', None)
            lang = request.GET.get('lang', 'pt').lower()
            item_type = request.GET.get('type', 'norm').lower()
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('pageSize', 50)), 200)

            # Validate language
            if lang not in ['pt', 'en']:
                return JsonResponse({
                    'error': 'Invalid language. Use "pt" or "en".'
                }, status=400)

            # Validate type
            if item_type not in ['norm', 'ipsa', 'scen']:
                return JsonResponse({
                    'error': 'Invalid type. Use "norm", "ipsa", or "scen".'
                }, status=400)

            # Map type to table
            table_map = {
                'norm': 'disc_items_norm',
                'ipsa': 'disc_blocks_ipsa',
                'scen': 'disc_scenarios'
            }
            table_name = table_map[item_type]

            # Get Supabase client
            supabase = get_supabase_client()

            # Get version reference if version specified
            version_ref = None
            if version:
                version_result = supabase.table('disc_versions').select('id').eq('version', version).execute()
                if not version_result.data:
                    return JsonResponse({
                        'error': f'Version "{version}" not found'
                    }, status=404)
                version_ref = version_result.data[0]['id']
            else:
                # Get latest version
                version_result = supabase.table('disc_versions').select('id, version').order('created_at', desc=True).limit(1).execute()
                if version_result.data:
                    version_ref = version_result.data[0]['id']
                    version = version_result.data[0]['version']

            if not version_ref:
                return JsonResponse({
                    'error': 'No DISC data available'
                }, status=404)

            # Build query
            query = supabase.table(table_name).select('*').eq('version_ref', version_ref)

            # Calculate pagination
            start = (page - 1) * page_size
            end = start + page_size - 1

            # Execute query with pagination
            result = query.range(start, end).execute()

            # Filter fields by language
            items = self._filter_by_language(result.data, lang)

            # Get total count (approximate from result)
            total = len(result.data) if len(result.data) < page_size else start + len(result.data) + 1

            return JsonResponse({
                'version': version,
                'lang': lang,
                'type': item_type,
                'page': page,
                'pageSize': page_size,
                'items': items,
                'hasMore': len(result.data) == page_size
            })

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.exception("Error in DISC bank API")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    def _filter_by_language(self, items: List[Dict], lang: str) -> List[Dict]:
        """Filter fields to return only requested language."""
        filtered = []

        for item in items:
            filtered_item = {}

            for key, value in item.items():
                # Skip internal fields
                if key in ['version_ref', 'created_at', 'id']:
                    continue

                # Handle bilingual fields
                if key.endswith('_pt'):
                    if lang == 'pt':
                        # Keep PT field without suffix
                        base_key = key[:-3]
                        filtered_item[base_key] = value
                elif key.endswith('_en'):
                    if lang == 'en':
                        # Keep EN field without suffix
                        base_key = key[:-3]
                        filtered_item[base_key] = value
                else:
                    # Keep non-language-specific fields
                    filtered_item[key] = value

            filtered.append(filtered_item)

        return filtered


class DISCTemplatesView(LoginRequiredMixin, View):
    """
    GET /api/disc/templates

    Query parameters:
        - version: Version string (default: latest)
        - lang: Language code 'pt' or 'en' (default: 'pt')

    Returns all templates and configuration data:
        - report_templates
        - thresholds
        - likert_map
        - words
        - interview
        - quality_checks
        - ethics
    """

    def get(self, request):
        try:
            # Parse query parameters
            version = request.GET.get('version', None)
            lang = request.GET.get('lang', 'pt').lower()

            # Validate language
            if lang not in ['pt', 'en']:
                return JsonResponse({
                    'error': 'Invalid language. Use "pt" or "en".'
                }, status=400)

            # Get Supabase client
            supabase = get_supabase_client()

            # Get version reference
            version_ref = None
            if version:
                version_result = supabase.table('disc_versions').select('id').eq('version', version).execute()
                if not version_result.data:
                    return JsonResponse({
                        'error': f'Version "{version}" not found'
                    }, status=404)
                version_ref = version_result.data[0]['id']
            else:
                # Get latest version
                version_result = supabase.table('disc_versions').select('id, version').order('created_at', desc=True).limit(1).execute()
                if version_result.data:
                    version_ref = version_result.data[0]['id']
                    version = version_result.data[0]['version']

            if not version_ref:
                return JsonResponse({
                    'error': 'No DISC data available'
                }, status=404)

            # Fetch all configuration data
            data = {}

            # Report templates
            templates_result = supabase.table('disc_report_templates').select('*').eq('version_ref', version_ref).execute()
            data['report_templates'] = self._filter_by_language(templates_result.data, lang)

            # Thresholds
            thresholds_result = supabase.table('disc_thresholds').select('*').eq('version_ref', version_ref).execute()
            data['thresholds'] = self._filter_by_language(thresholds_result.data, lang)

            # Likert map
            likert_result = supabase.table('disc_likert_map').select('*').eq('version_ref', version_ref).execute()
            data['likert_map'] = self._filter_by_language(likert_result.data, lang)

            # Words
            words_result = supabase.table('disc_words').select('*').eq('version_ref', version_ref).execute()
            data['words'] = self._filter_by_language(words_result.data, lang)

            # Interview guide
            interview_result = supabase.table('disc_interview').select('*').eq('version_ref', version_ref).execute()
            data['interview'] = self._filter_by_language(interview_result.data, lang)

            # Quality checks
            quality_result = supabase.table('disc_quality_checks').select('*').eq('version_ref', version_ref).execute()
            data['quality_checks'] = self._filter_by_language(quality_result.data, lang)

            # Ethics
            ethics_result = supabase.table('disc_ethics').select('*').eq('version_ref', version_ref).execute()
            data['ethics'] = self._filter_by_language(ethics_result.data, lang)

            # Rules
            rules_result = supabase.table('disc_rules').select('*').eq('version_ref', version_ref).execute()
            data['rules'] = self._filter_by_language(rules_result.data, lang)

            return JsonResponse({
                'version': version,
                'lang': lang,
                'data': data
            })

        except Exception as e:
            logger.exception("Error in DISC templates API")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    def _filter_by_language(self, items: List[Dict], lang: str) -> List[Dict]:
        """Filter fields to return only requested language."""
        filtered = []

        for item in items:
            filtered_item = {}

            for key, value in item.items():
                # Skip internal fields
                if key in ['version_ref', 'created_at', 'id']:
                    continue

                # Handle bilingual fields
                if key.endswith('_pt'):
                    if lang == 'pt':
                        # Keep PT field without suffix
                        base_key = key[:-3]
                        filtered_item[base_key] = value
                elif key.endswith('_en'):
                    if lang == 'en':
                        # Keep EN field without suffix
                        base_key = key[:-3]
                        filtered_item[base_key] = value
                else:
                    # Keep non-language-specific fields
                    filtered_item[key] = value

            filtered.append(filtered_item)

        return filtered
