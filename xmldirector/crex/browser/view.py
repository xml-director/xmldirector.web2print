# -*- coding: utf-8 -*-

################################################################
# xmldirector.bookalope
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import os
import fs.zipfs
import tempfile

from Products.Five.browser import BrowserView

from xmldirector.crex.browser.restapi import delete_after
from xmldirector.crex.browser.restapi import convert_crex
from xmldirector.crex.browser.restapi import store_zip
from xmldirector.crex.browser.restapi import ENDPOINTS


class CREX(BrowserView):

    def upload_source(self):

        source = self.request.get('source')
        if not source:
            raise ValueError('No file uploaded')

        basename, ext = os.path.splitext(os.path.basename(source.filename))
        if not ext.lower().endswith('.docx'):
            raise ValueError('Uploaded files must be DOCX')

        handle = self.context.get_handle()
        if not handle.exists('src'):
            handle.makedir('src')

        filename = 'src/index.docx'
        with handle.open(filename, 'wb') as fp:
            source.seek(0)
            fp.write(source.read())

        self.context.plone_utils.addPortalMessage(u'Upload completed')
        self.request.response.redirect(self.context.absolute_url() + '/@@xmldirector-crex')

    def get_source_files(self):
        handle = self.context.get_handle()
        if not handle.exists('src'):
            return ()
        return sorted(['src/{}'.format(name) for name in handle.listdir('src') if name.endswith('.docx')])

    def get_generated_files(self):
        handle = self.context.get_handle()
        if not handle.exists('result'):
            return ()
        return sorted(['result/{}'.format(name) for name in handle.listdir('result')])

    def cleanup_generated_files(self):
        handle = self.context.get_handle()
        if handle.exists('result'):
            handle.removedir('result', force=True, recursive=True)
        self.context.plone_utils.addPortalMessage(u'Generated files removed')
        self.request.response.redirect(self.context.absolute_url() + '/@@xmldirector-crex')

    def cleanup_source_files(self):
        handle = self.context.get_handle()
        if handle.exists('src'):
            for name in handle.listdir('src'):
                if name.endswith('.docx'):
                    handle.remove('src/{}'.format(name))
        self.context.plone_utils.addPortalMessage(u'Source files removed')
        self.request.response.redirect(self.context.absolute_url() + '/@@xmldirector-crex')

    def get_endpoints(self):
        return ENDPOINTS

    def convert(self):

        endpoint = self.request['endpoint']
        endpoint_url = ENDPOINTS[endpoint]['url']
        handle = self.context.get_handle()

        if not handle.exists('src/index.docx'):
            raise ValueError('No file src/index.docx found')

        zip_tmp = tempfile.mktemp(suffix='.zip')
        with fs.zipfs.ZipFS(zip_tmp, 'w') as zip_fp:
            with zip_fp.open('src/index.docx', 'wb') as fp_out:
                fp_out.write(handle.open('src/index.docx', 'rb').read())

        with delete_after(zip_tmp):
            zip_out = convert_crex(zip_tmp, crex_url=endpoint_url)

        store_zip(self.context, zip_out, 'result')

        self.context.plone_utils.addPortalMessage(u'Conversion completed')
        self.request.response.redirect(self.context.absolute_url() + '/@@xmldirector-crex')

