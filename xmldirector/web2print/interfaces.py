# -*- coding: utf-8 -*-

################################################################
# xmldirector.web2print
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

from zope.interface import Interface
from zope import schema
from xmldirector.web2print.i18n import MessageFactory as _


class IBrowserLayer(Interface):
    """A brower layer specific to my product """


class IWeb2PrintSettings(Interface):
    """ Web2Print settings """

#    web2print_conversion_url = schema.TextLine(
#        title=_(u'URL for C-REX conversion webservice'),
#        description=_(u'URL for C-REX conversion webservice'),
#        default=u'https://c-rex.net/api/XBot/Convert/DGHO/docxMigration'
#    )
