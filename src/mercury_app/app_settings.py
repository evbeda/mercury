from mercury_site.__init__ import get_env_variable

# Webhook related settings
URL_LOCAL = get_env_variable('URL_LOCAL')
URL_ENDPOINT_ORDER = URL_LOCAL + '/webhook-order/'
URL_ENDPOINT_CHECK_IN = URL_LOCAL + '/webhook-checkin/'
WH_ORDER_ACTION = 'order.placed'
WH_CHECK_IN_ACTION = 'barcode.checked_in'
WH_TYPE = (
    ('CH', 'Check In'),
    ('OR', 'Order Placed'),
)
# REDIS related settings
REDIS_URL = get_env_variable('REDIS_URL')
BROKER_URL = REDIS_URL  # + '/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_BROKER_URL = BROKER_URL
CELERY_RESULT_BACKEND = BROKER_URL
# DO NOT uncomment this line, it turns async tasks into sync
CELERY_TASK_ALWAYS_EAGER = True

REGEX_ORDER = r'(http[s]?:\/\/)?([^\/\s]+\/)([^\/\s]+\/)([^\/\s]+\/)(\d+)(.*)'
REGEX_CHECK_IN = r'(http[s]?:\/\/)?([^\/\s]+\/)([^\/\s]+\/)([^\/\s]+\/)(\w+)(.*)([^\/\s]+\/)([\d\-]+)'