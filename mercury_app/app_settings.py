from mercury_site.__init__ import get_env_variable

# Webhook related settings
URL_LOCAL = get_env_variable('URL_LOCAL')
URL_ENDPOINT = URL_LOCAL + '/webhook-point/'
WH_ACTIONS = 'order.placed'

# REDIS related settings
REDIS_URL = get_env_variable('REDIS_URL')
BROKER_URL = REDIS_URL  # + '/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_BROKER_URL = BROKER_URL
CELERY_RESULT_BACKEND = BROKER_URL
# DO NOT uncomment this line, it turns async tasks into sync
# CELERY_TASK_ALWAYS_EAGER = True

REGEX_ORDER = r'(http[s]?:\/\/)?([^\/\s]+\/)([^\/\s]+\/)([^\/\s]+\/)(\d+)(.*)'
