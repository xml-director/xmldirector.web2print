# -*- coding: utf-8 -*-

################################################################
# xmldirector.web2print
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import logging

LOG = logging.getLogger('xmldirector.web2print')

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
urllib3_log = logging.getLogger("urllib3")
urllib3_log.setLevel(logging.WARNING)
