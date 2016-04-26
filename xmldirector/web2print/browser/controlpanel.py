# -*- coding: utf-8 -*-


################################################################
# xmldirector.web2print
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

from plone.app.registry.browser import controlpanel

from xmldirector.web2print.interfaces import IWeb2PrintSettings
from xmldirector.web2print.i18n import MessageFactory as _


class Web2PrintSettingsEditForm(controlpanel.RegistryEditForm):

    schema = IWeb2PrintSettings
    label = _(u'Web2Print Policy settings')
    description = _(u'')

    def updateFields(self):
        super(Web2PrintSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(Web2PrintSettingsEditForm, self).updateWidgets()


class Web2PrintSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = Web2PrintSettingsEditForm
