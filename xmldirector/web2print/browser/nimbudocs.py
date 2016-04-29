# -*- coding: utf-8 -*-

################################################################
# xmldirector.web2print
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import os
import furl
import fs.path
import json
import datetime
import requests
import shutil
import tempfile
import hurry
import humanize
import fs.path
import lxml.html

import plone.api
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from pp.client.plone.interfaces import IPPClientPloneSettings

from pp.client.python.pdf import pdf


class Nimbudocs(BrowserView):

    def actionmap_json(self):
        """ Provide modified actionMap.ext.json for Nimbudocs editor """
        json_fn = os.path.join(os.path.dirname(__file__), 'resources', 'extensions', 'actionMap.ext.json')
        with open(json_fn, 'rb') as fp:
            data = json.load(fp)
        portal_url = plone.api.portal.get().absolute_url()
        data['save-and-close']['iconUrl']  = portal_url + '/' + data['save-and-close']['iconUrl']
        data['local-save']['iconUrl']  = portal_url + '/' + data['local-save']['iconUrl']
        data['local-restore']['iconUrl']  = portal_url + '/' + data['local-restore']['iconUrl']
        data['exit']['iconUrl']  = portal_url + '/' + data['exit']['iconUrl']
        self.request.response.setHeader('content-type', 'application/json')
        self.request.response.write(json.dumps(data))

    def set_content(self, *args, **kw):

        html = self.request['html']
        pdf_url = self.request['pdf_url']
        template = self.request['template']
        handle = self.context.get_handle()

        result = requests.get(pdf_url)
        if result.status_code == 200:
            # write PDF + HTML
            template_id, ext = os.path.splitext(os.path.basename(template))
            now = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')                        
            output_filename = 'output/{}-{}.html'.format(template_id, now)
            with handle.open(output_filename, 'wb') as fp:
                fp.write(html)
            output_filename = 'output/{}-{}.pdf'.format(template_id, now)
            with handle.open(output_filename, 'wb') as fp:
                fp.write(result.content)
            # redirection url
            f = furl.furl('{}/@@xmldirector-web2print'.format(self.context.absolute_url()))
            f.args['template'] = template
            f.args['output_url'] = '{}/@@view/{}'.format(self.context.absolute_url(), output_filename)
            f.add(fragment_path='pdf-files')
            self.request.response.setStatus(200)                                               
            return str(f)
        else:
            self.request.response.setStatus(500)

