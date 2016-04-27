# -*- coding: utf-8 -*-

################################################################
# xmldirector.web2print
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import os
import furl
import fs.path
import datetime
import shutil
import tempfile
import hurry
import humanize
import fs.path
import lxml.html

from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from pp.client.plone.interfaces import IPPClientPloneSettings

from pp.client.python.pdf import pdf


class Web2Print(BrowserView):

    def human_readable_filesize(self, num_bytes):
        """ Return num_bytes as human readable representation """
        return hurry.filesize.size(num_bytes, hurry.filesize.alternative)

    def human_readable_datetime(self, dt=None, to_utc=False):
        """ Convert with `dt` datetime string into a human readable
            representation using humanize module.
        """
        if dt:
            if to_utc:
                diff = datetime.datetime.utcnow() - dt
                return humanize.naturaltime(diff)
            else:
                return humanize.naturaltime(dt)

    def all_pdf_files(self, output_dir='output'):
        """ List all PDF files templates """
        result = list()
        handle = self.context.get_handle(output_dir)
        generator = handle.ilistdirinfo(files_only=True, wildcard='*pdf')
        context_url = self.context.absolute_url()
        for name, info in generator:
            url = '{}/raw/{}/{}'.format(context_url, output_dir, name)
            result.append(dict(
                 url=url,
                 title=name,
                 created=info.get('created_time'),
                 size=info.get('st_size')))
        return sorted(result, key=lambda x: x.get('size', 0))

    def available_templates(self, template_dir='templates'):
        """ List all available templates """
        result = list()
        handle = self.context.get_handle(template_dir)
        files = handle.listdir(files_only=True, wildcard='*html')
        for name in sorted(files):

            # extract <title> from HTML
            with handle.open(name, 'rb') as fp:
                root = lxml.html.fromstring(fp.read())
            nodes = root.xpath('//title')
            title = name
            if nodes:
                title = nodes[0].text

            image_id = fs.path.join(template_dir, os.path.splitext(name)[0] + '.png')
            result.append(dict(
                id=fs.path.join(template_dir, name), 
                title=title,
                image_id=image_id))
        return result

    def cleanup_output_directory(self, output_dir='output'):
        """ Cleanup output directory """

        handle = self.context.get_handle()
        handle.removedir(output_dir, force=True)
        handle.makedir(output_dir)
        self.context.plone_utils.addPortalMessage(u'Conversion successful')
        self.request.response.redirect(self.context.absolute_url() + '/@@xmldirector-web2print')


    def parse_template(self, template=None):

        template = self.request.form.get('template')  or template
        if not template:
            raise ValueError('No template given')

        handle = self.context.get_handle()
        with handle.open(template, 'rb') as fp:
            root = lxml.html.fromstring(fp.read())

        result = list()
        for node in root.xpath('//*[@editable="yes"]'):

            node_id = node.attrib.get('id')
            if not node_id:
                raise ValueError(u'Missing id attribute in {}'.format(lxml.html.tostring(node)))

            node_type = node.attrib.get('type', 'string')
            if node_type not in ('string', 'text', 'email', 'float', 'integer'):
                raise ValueError(u'Unknown type="{}" in {}'.format(node_type, lxml.html.tostring(node)))

            node_placeholder = node.attrib.get('placeholder', node_id)
            node_required = not node.attrib.get('required', 'yes') == 'no'
            node_use_default = node.attrib.get('use_default', 'no') == 'yes'
            node_text = node.text if node_use_default else u''
            result.append(dict(
                id=node_id,
                required=node_required,
                placeholder=node_placeholder,
                text=node_text,
                type=node_type))
        return result

    def generate_pdf(self):

        handle = self.context.get_handle()

        template = self.request.form.get('template')  or template
        if not template:
            raise ValueError('No template given')

        handle = self.context.get_handle()
        with handle.open(template, 'rb') as fp:
            root = lxml.html.fromstring(fp.read())

        for k, v in self.request.form.items():
            node = root.find('.//*[@id="{}"]'.format(k))
            if node is not None:
                node.text = unicode(v, 'utf8')

        # copy resources
        temp_dir = tempfile.mktemp()
        template_dir = os.path.dirname(template)
        for name in handle.walkfiles(template_dir):
            target_filename = os.path.join(temp_dir, name.replace(template_dir + '/', ''))
            if not os.path.exists(os.path.dirname(target_filename)):
                os.makedirs(os.path.dirname(target_filename))
            with handle.open(name, 'rb') as fp_in:
                with open(target_filename, 'wb') as fp_out:
                    fp_out.write(fp_in.read())

        # write index.html
        with open(os.path.join(temp_dir, 'index.html'), 'wb') as fp:
            fp.write(lxml.html.tostring(root, encoding='utf8'))
                                                                                                                                               
        # Read Produce & Publish server URL settings from Plone registry
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IPPClientPloneSettings)
        sf = furl.furl(settings.server_url)
        if settings.server_username:
            sf.username = settings.server_username
        if settings.server_password:
            sf.password = settings.server_password

        # run PDF conversion on remote Produce & Publish server
        cmd_options = '-j -A "XML Director Web2Print"'
        result = pdf(source_directory=temp_dir,
                     converter='pdfreactor',
                     cmd_options=cmd_options,
                     server_url=sf.url,
                     ssl_cert_verification=True,
                     verbose=True)
        
        if result['status'] == 'OK':
            if not handle.exists('output'):
                handle.makedir('output')

            output_filename = 'output/{}.pdf'.format(datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S'))                        
            with open(result['output_filename'], 'rb') as fp_in:
                with handle.open(output_filename, 'wb') as fp_out:
                    fp_out.write(fp_in.read())

            self.context.plone_utils.addPortalMessage(u'Conversion successful')
        else:
            self.context.plone_utils.addPortalMessage(u'Conversion error', 'error')

        f = furl.furl(self.context.absolute_url() + '/@@xmldirector-web2print')
        f.args = self.request.form
        f.args['output_url'] = '{}/@@view/{}'.format(self.context.absolute_url(), output_filename)
        self.request.response.redirect(str(f))
