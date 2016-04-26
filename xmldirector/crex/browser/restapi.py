# -*- coding: utf-8 -*-

################################################################
# xmldirector.crex
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import os
import time
import furl
from collections import OrderedDict
import datetime
import requests
import fs.zipfs

import plone.api
import transaction
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.annotation.interfaces import IAnnotations
from Products.CMFCore import permissions
from ZPublisher.Iterators import filestream_iterator

from xmldirector.crex.logger import LOG
from xmldirector.crex.interfaces import ICRexSettings
from xmldirector.crex.browser.rewriterules import RuleRewriter
from zopyx.plone.persistentlogger.logger import IPersistentLogger

from xmldirector.plonecore.browser.restapi import temp_zip
from xmldirector.plonecore.browser.restapi import delete_after
from xmldirector.plonecore.browser.restapi import BaseService
from xmldirector.plonecore.browser.restapi import store_zip
from xmldirector.plonecore.browser.restapi import decode_json_payload

from collective.taskqueue import taskqueue


ANNOTATION_CREX_INFO_KEY = 'xmldirector.plonecore.crex.queue'

CREX_STATUS_PENDING = u'pending'
CREX_STATUS_RUNNING = u'running'
CREX_STATUS_ERROR = u'error'
CREX_STATUS_SUCCESS = u'success'


ENDPOINTS = OrderedDict()
ENDPOINTS['docx2onkopedia'] = \
        dict(url='https://www.c-rex.net/api/XBot/Convert//Demo.XmlDirector/XmlDirector',
             title=u'DOCX to Onkopedia XML')
ENDPOINTS['docx2ditatopic'] = \
        dict(url='https://www.c-rex.net/api/XBot/Convert/Demo/docx2DITATopic',
             title=u'DOCX to DITA topic')
ENDPOINTS['docx2ditamap'] = \
        dict(url='https://www.c-rex.net/api/XBot/Convert/Demo/docx2DITAMap',
             title=u'DOCX to DITA map')


class CRexConversionError(Exception):
    """ A generic C-Rex error """


def convert_crex(zip_path, crex_url=None, crex_username=None, crex_password=None):
    """ Send ZIP archive with content to be converted to C-Rex.
        Returns name of ZIP file with converted resources.
    """

    ts = time.time()
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ICRexSettings)

    crex_conversion_url = crex_url or settings.crex_conversion_url
    crex_conversion_username = crex_username or settings.crex_conversion_username
    crex_conversion_password = crex_password or settings.crex_conversion_password
    crex_token = settings.crex_conversion_token

    # Fetch authentication token if necessary (older than one hour)
    crex_token_last_fetched = settings.crex_conversion_token_last_fetched or datetime.datetime(
        2000, 1, 1)
    diff = datetime.datetime.utcnow() - crex_token_last_fetched

    if not crex_token or diff.total_seconds() > 3600:
        f = furl.furl(crex_conversion_url)
        token_url = '{}://{}/api/Token'.format(
            f.scheme, f.host, crex_conversion_url)
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        params = dict(
            username=crex_conversion_username,
            password=crex_conversion_password,
            grant_type='password')
        result = requests.post(token_url, data=params, headers=headers)
        if result.status_code != 200:
            msg = u'Error retrieving DOCX conversion token from webservice (HTTP code {}, Message {})'.format(
                result.status_code, result.text)
            LOG.error(msg)
            raise CRexConversionError(msg)
        data = result.json()
        crex_token = data['access_token']
        settings.crex_conversion_token = crex_token
        settings.crex_conversion_token_last_fetched = datetime.datetime.utcnow()
        LOG.info('Fetching new DOCX authentication token - successful')
    else:
        LOG.info('Fetching DOCX authentication token from Plone cache')

    headers = {'authorization': 'Bearer {}'.format(crex_token)}

    with open(zip_path, 'rb') as fp:
        try:
            LOG.info(u'Starting C-Rex conversion of {}, size {} '.format(zip_path,
                                                                         os.path.getsize(zip_path)))
            result = requests.post(
                crex_conversion_url, files=dict(source=fp), headers=headers)
        except requests.ConnectionError:
            msg = u'Connection to C-REX webservice failed'
            raise CRexConversionError(msg)

        if result.status_code == 200:
            msg = u'Conversion successful (HTTP code {}, duration: {:2.1f} seconds))'.format(
                result.status_code, time.time() - ts)
            LOG.info(msg)
            zip_out = temp_zip(suffix='.zip')
            with open(zip_out, 'wb') as fp:
                fp.write(result.content)
            return zip_out

        else:
            # Forbidden -> invalid token -> invalidate token stored in Plone
            if result.status_code == 401:
                settings.crex_conversion_token = u''
                settings.crex_conversion_token_last_fetched = datetime.datetime(
                    1999, 1, 1)
            msg = u'Conversion failed (HTTP code {}, message {})'.format(
                result.status_code, result.text)
            LOG.error(msg)
            raise CRexConversionError(msg)


class BaseService(BaseService):
    """ Base class for REST services """

    def get_crex_info(self):
        annotations = IAnnotations(self.context)
        return annotations.get(ANNOTATION_CREX_INFO_KEY, {})

    def set_crex_info(self, info):
        annotations = IAnnotations(self.context)
        annotations[ANNOTATION_CREX_INFO_KEY] = info


class api_convert(BaseService):

    def _render(self):

        conversion_info = self.get_crex_info()
        conversion_info['status'] = CREX_STATUS_RUNNING
        conversion_info[
            'running_since'] = datetime.datetime.utcnow().isoformat()
        self.set_crex_info(conversion_info)
        transaction.commit()

        try:
            result = self._render2()
            conversion_info['status'] = CREX_STATUS_SUCCESS
            conversion_info[
                'terminated'] = datetime.datetime.utcnow().isoformat()
            self.set_crex_info(conversion_info)
            return result
        except Exception as e:
            LOG.error(e, exc_info=True)
            conversion_info['status'] = CREX_STATUS_ERROR
            conversion_info[
                'terminated'] = datetime.datetime.utcnow().isoformat()
            conversion_info['error'] = str(e)
            self.set_crex_info(conversion_info)
            transaction.commit()
            raise

    def _render2(self):

        IPersistentLogger(self.context).log('convert')
        payload = decode_json_payload(self.request)

        if 'mapping' not in payload:
            raise ValueError('No "mapping" found in JSON payload')

        rules = payload['mapping']
        conversion_id = payload.get('converter', 'docx2ditatopic')
        conversion_endpoint_url = ENDPOINTS[conversion_id]['url']
        rewriter = RuleRewriter(rules)

        handle = self.context.webdav_handle()
        zip_tmp = temp_zip(suffix='.zip')
        with fs.zipfs.ZipFS(zip_tmp, 'w') as zip_fp:
            for name in handle.walkfiles():
                if name.endswith('.sha256'):
                    continue
                name_in_zip = rewriter.rewrite(name)
                if name_in_zip:
                    with handle.open(name, 'rb') as fp_in, \
                            zip_fp.open(name_in_zip, 'wb') as fp:
                        fp.write(fp_in.read())

        
        with delete_after(zip_tmp):
            zip_out = convert_crex(zip_tmp, crex_url=conversion_endpoint_url)
        store_zip(self.context, zip_out, 'current')

        conversion_info = self.get_crex_info()
        conversion_info['status'] = CREX_STATUS_SUCCESS
        self.set_crex_info(conversion_info)

        with delete_after(zip_out):
            self.request.response.setHeader(
                'content-length', str(os.path.getsize(zip_out)))
            self.request.response.setHeader('content-type', 'application/zip')
            self.request.response.setHeader(
                'content-disposition', 'attachment; filename={}.zip'.format(self.context.getId()))
            return filestream_iterator(zip_out)


class api_convert_async(BaseService):

    def _render(self):

        conversion_information = self.get_crex_info()
        status = conversion_information.get('status')
        if not status or status in (CREX_STATUS_ERROR, CREX_STATUS_SUCCESS):
            task_id = taskqueue.add(
                url=self.context.absolute_url(1) + '/xmldirector-convert',
                method=self.request.REQUEST_METHOD,
                headers={'accept': 'application/json',
                         'content-type': 'application/json'},
                payload=self.request.BODY,
                params=dict(status=u'async', msg=u'Queued')
            )
            data = {'task_id': task_id,
                    'created': datetime.datetime.utcnow().isoformat(),
                    'creator': plone.api.user.get_current().getUserName(),
                    'status': u'spooled'}
            self.set_crex_info(data)
            return data
        else:
            self.request.response.setStatus(409)  # Conflict
            data = conversion_information.copy()
            data['msg'] = u'Conversion request could not be spooled'
            return data


class api_convert_status(BaseService):

    def _render(self):

        return self.get_crex_info()
