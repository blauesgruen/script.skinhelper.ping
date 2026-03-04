from default import Hosts
import xbmc
import xbmcaddon


class PingMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self._reload_setting()

    def _reload_setting(self):
        self.is_service = xbmcaddon.Addon(id='script.skinhelper.ping').getSetting('service').upper() == 'TRUE'

    def onSettingsChanged(self):
        self._reload_setting()


mon = PingMonitor()
xbmc.log('[script.skinhelper.ping] Service started', xbmc.LOGINFO)

while not mon.abortRequested():
    if mon.is_service:
        hosts = Hosts()
        xbmc.log('[script.skinhelper.ping] %s/%s Servers active' % (hosts.serveron, hosts.servercount), xbmc.LOGDEBUG)

    if mon.waitForAbort(10):
        xbmc.log('[script.skinhelper.ping] Service stopped')
        break
