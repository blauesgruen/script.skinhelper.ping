# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcvfs
import sys
import os
import platform
import subprocess
import xbmcgui

__addon__ = xbmcaddon.Addon()
__addon_id__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__addonpath__ = xbmcvfs.translatePath(__addon__.getAddonInfo('path'))
__loc__ = __addon__.getLocalizedString

icon_on = os.path.join(__addonpath__, 'resources', 'media', 'online.png')
icon_off = os.path.join(__addonpath__, 'resources', 'media', 'offline.png')

WINDOW = xbmcgui.Window(10000)


def wol(mac):
    if not mac:
        xbmc.log('[script.skinhelper.ping] WOL: keine MAC-Adresse konfiguriert', xbmc.LOGWARNING)
        return
    xbmc.executebuiltin("WakeOnLan({})".format(mac))


def ping(current_ip_address, timeout=5):
    count = 'n' if platform.system().lower() == 'windows' else 'c'
    try:
        subprocess.run("ping -{} 1 {}".format(count, current_ip_address), shell=True, check=True, timeout=timeout)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        xbmc.log('Ping returns an error: {}'.format(e), xbmc.LOGERROR)
        return False


class Hosts:

    def __init__(self):
        self.servercount = 0
        self.serveron = 0
        self.serveroff = 0
        self.host = list()

        for host_nr in range(0, 5):
            self.host.append([__addon__.getSetting('ip{}'.format(host_nr + 1)),
                                __addon__.getSetting('mac{}'.format(host_nr + 1)),
                                __addon__.getSetting('name{}'.format(host_nr + 1)),
                                icon_off])

            if self.host[host_nr][0] != '':
                self.servercount += 1
                if ping(self.host[host_nr][0], timeout=1):
                    WINDOW.setProperty('SkinHelperPing.server{}'.format(host_nr + 1), 'on')
                    self.host[host_nr][3] = icon_on
                    self.serveron += 1
                else:
                    WINDOW.setProperty('SkinHelperPing.server{}'.format(host_nr + 1), 'off')
                    self.serveroff += 1

            WINDOW.setProperty('SkinHelperPING.ip{}'.format(host_nr + 1), self.host[host_nr][0])
            WINDOW.setProperty('SkinHelperPING.mac{}'.format(host_nr + 1), self.host[host_nr][1])
            WINDOW.setProperty('SkinHelperPING.servername{}'.format(host_nr + 1), self.host[host_nr][2])

        WINDOW.setProperty("SkinHelperPING.servercount", str(self.servercount))
        WINDOW.setProperty("SkinHelperPING.serveron", str(self.serveron))
        WINDOW.setProperty("SkinHelperPING.serveroff", str(self.serveroff))


if __name__ == '__main__':
    hosts = Hosts()
    try:
        param = sys.argv[1]
        if param == "status":
            exit(0)
        elif param[0:3] == "wol":
            host_nr = int(param[-1:]) - 1
            xbmc.log('Send WOL packet to {} (MAC {})'.format(hosts.host[host_nr][2], hosts.host[host_nr][1]), xbmc.LOGINFO)
            wol(hosts.host[host_nr][1])
        else:
            xbmc.log('Wrong parameter: {}'.format(param), xbmc.LOGERROR)

    except IndexError:
        host_list = list()
        for host_nr in range(0, 5):
            if hosts.host[host_nr][0] == '': continue
            liz = xbmcgui.ListItem(label=hosts.host[host_nr][2], label2=hosts.host[host_nr][0])
            liz.setProperty('mac', hosts.host[host_nr][1])
            liz.setArt({'icon': hosts.host[host_nr][3]})
            host_list.append(liz)

        if len(host_list) > 0:
            _idx = xbmcgui.Dialog().select(__loc__(32010), host_list, useDetails=True)
            if _idx > -1:
                wol(host_list[_idx].getProperty('mac'))
        else:
            xbmcgui.Dialog().ok(__addonname__, __loc__(32011))
