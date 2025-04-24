import logging
logger = logging.getLogger('django')


# 람다 환경 요청 호스트 확인용 middleware
# todo: 나중에 필요 없을 때 지우기
def debug_middleware(get_response):
    def middleware(request):
        # 요청 헤더 로깅
        logger.info(f"DEBUG - Host: {request.META.get('HTTP_HOST')}")
        logger.info(f"DEBUG - X-Forwarded-Host: {request.META.get('HTTP_X_FORWARDED_HOST')}")
        logger.info(f"DEBUG - All headers: {request.META}")

        response = get_response(request)
        return response
    return middleware