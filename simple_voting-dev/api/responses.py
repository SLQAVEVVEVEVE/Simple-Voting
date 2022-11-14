from django.http import JsonResponse

class APIResponseTemplate:
    @staticmethod
    def error(detail='Unknown error occured', data=None):
        return {
            'success': False,
            'detail': detail,
            'data': data if data else {}
        }

    @staticmethod
    def success(detail='', data=None):
        return {
            'success': True,
            'detail': detail,
            'data': data if data else {}
        }

class GenericAPIResponses:
    OK = JsonResponse(APIResponseTemplate.success(), status=200)
    CREATED = JsonResponse(APIResponseTemplate.success(), status=201)

    METHOD_NOT_ALLOWED = JsonResponse({
        'success': False,
        'detail': 'Method not allowed',
        'data': {}
    }, status=405)

    AUTHENTICATION_REQUIRED = JsonResponse({
        'success': False,
        'detail': 'Authentication required to perform this action',
        'data': {}
    }, status=401)

    def invalid_form(form):
        return JsonResponse({
            'success': False,
            'detail': 'Form is invalid',
            'data': {
                'errors': form.errors.as_json()
            }
        }, status=422)
