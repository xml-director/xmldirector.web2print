# -*- coding: utf-8 -*-

################################################################
# xmldirector.web2print
# (C) 2015,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


from Products.Five.browser import BrowserView


class Queue(BrowserView):

    def queue(self):
        print 'INSIDE QUEUE'
