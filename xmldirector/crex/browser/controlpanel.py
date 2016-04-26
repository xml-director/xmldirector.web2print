# -*- coding: utf-8 -*-


################################################################
# xmldirector.crex
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

from plone.app.registry.browser import controlpanel

from xmldirector.crex.interfaces import ICRexSettings
from xmldirector.crex.i18n import MessageFactory as _


class CRexSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ICRexSettings
    label = _(u'CRex Policy settings')
    description = _(u'')

    def updateFields(self):
        super(CRexSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(CRexSettingsEditForm, self).updateWidgets()


class CRexSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = CRexSettingsEditForm
