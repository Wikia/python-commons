wikia.common.logger
===================

Common logging classes for centralized logging at Wikia

Logging to kibana from your k8s pods.
------------------------------------

You can use ``WikiaJsonLogsFormatter`` as a convenient way of logging from k8s pods. to kibana.
  
Add to ``requirements.txt``::

  wikia-common-logger==1.0.2

Install requirements in your ``Dockerfile``::
  
  RUN pip install --index-url https://artifactory.wikia-inc.com/artifactory/api/pypi/pypi/simple -r requirements.txt

Import ``json_logger`` in your python app::

  from wikia.common.logger import json_logger

Set the logger and use it in pythonic way::

  json_logger.configure('my_app_name', '0.32.0', 'INFO')
  logger = logging.getLogger(__name__)
  logger.info('App has started')
  
