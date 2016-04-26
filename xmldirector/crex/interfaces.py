# -*- coding: utf-8 -*-

################################################################
# onkopedia.crex
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

from zope.interface import Interface
from zope import schema
from xmldirector.crex.i18n import MessageFactory as _


class IBrowserLayer(Interface):
    """A brower layer specific to my product """


class ICRexSettings(Interface):
    """ C-Rex settings """

    crex_conversion_url = schema.TextLine(
        title=_(u'URL for C-REX conversion webservice'),
        description=_(u'URL for C-REX conversion webservice'),
        default=u'https://c-rex.net/api/XBot/Convert/DGHO/docxMigration'
    )

    crex_conversion_username = schema.TextLine(
        title=_(u'Username for C-REX conversion webservice'),
        description=_(u'Username for C-REX conversion webservice'),
        default=u''
    )

    crex_conversion_password = schema.TextLine(
        title=_(u'Password for C-REX conversion webservice'),
        description=_(u'Password for C-REX conversion webservice'),
        default=u''
    )

    crex_conversion_token = schema.TextLine(
        title=_(u'C-REX Conversion Token'),
        description=_(u'C-REX Conversion Token'),
        default=u'',
        required=False
    )

    crex_conversion_token_last_fetched = schema.Datetime(
        title=_(u'DateTime C-Rex conversion toked fetched'),
        description=_(u'DateTime C-Rex conversion toked fetched'),
        required=False
    )
