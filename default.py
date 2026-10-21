# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcvfs
import sys
import os
import platform
import re
import subprocess
import xbmcgui
from resources import network_scan

__addon__ = xbmcaddon.Addon()
__addon_id__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__addonpath__ = xbmcvfs.translatePath(__addon__.getAddonInfo('path'))
__loc__ = __addon__.getLocalizedString

icon_on = os.path.join(__addonpath__, 'resources', 'media', 'online.png')
icon_off = os.path.join(__addonpath__, 'resources', 'media', 'offline.png')

WINDOW = xbmcgui.Window(10000)
PROPERTY_PREFIX = 'SkinHelperPING'
MAC_ADDRESS_PATTERN = re.compile(r'^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$')


def wol(mac):
    if not mac or not MAC_ADDRESS_PATTERN.match(mac):
        xbmc.log('[script.skinhelper.ping] WOL: keine gültige MAC-Adresse konfiguriert', xbmc.LOGWARNING)
        return
    normalized_mac = mac.replace('-', ':').upper()
    xbmc.executebuiltin("WakeOnLan({})".format(normalized_mac))


def ping(current_ip_address, timeout=5):
    count = 'n' if platform.system().lower() == 'windows' else 'c'
    try:
        subprocess.run(
            ['ping', '-{}'.format(count), '1', current_ip_address],
            check=True,
            timeout=timeout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        xbmc.log('Ping returns an error: {}'.format(e), xbmc.LOGERROR)
        return False


def _normalized_mac(mac):
    return (mac or '').replace('-', ':').replace(':', '').lower()


def scan_network_and_add_device():
    dialog = xbmcgui.Dialog()
    free_slots = [
        number for number in range(1, 6)
        if not any(__addon__.getSetting('{}{}'.format(key, number)).strip() for key in ('ip', 'mac', 'name'))
    ]
    if not free_slots:
        dialog.ok(__addonname__, __loc__(32025))
        return

    networks = network_scan.get_networks()
    if not networks:
        dialog.ok(__addonname__, __loc__(32026))
        return
    if len(networks) == 1:
        selected_network = networks[0]
    else:
        labels = [
            '{} — {}/{}'.format(item['interface'], item['address'], item['network'].prefixlen)
            for item in networks
        ]
        selection = dialog.select(__loc__(32016), labels)
        if selection < 0:
            return
        selected_network = networks[selection]

    host_count = selected_network['network'].num_addresses - 2
    if selected_network['network'].prefixlen >= 31:
        host_count = selected_network['network'].num_addresses - 1
    if host_count > network_scan.MAX_SCAN_HOSTS:
        dialog.ok(__addonname__, __loc__(32017).format(host_count, network_scan.MAX_SCAN_HOSTS))
        return

    progress = xbmcgui.DialogProgress()
    progress.create(__addonname__, __loc__(32018).format(selected_network['network']))

    def update_progress(completed, total):
        percent = int(completed * 100 / total) if total else 100
        progress.update(percent, __loc__(32019).format(completed, total))

    try:
        found = network_scan.scan_network(
            selected_network,
            update_progress,
            progress.iscanceled,
        )
    except Exception as error:
        xbmc.log('[script.skinhelper.ping] Network scan failed: {}'.format(error), xbmc.LOGERROR)
        found = []
    finally:
        progress.close()

    if found is None:
        dialog.ok(__addonname__, __loc__(32020))
        return
    if not found:
        dialog.ok(__addonname__, __loc__(32021))
        return

    items = [
        '{} — {} — {}'.format(item['name'], item['ip'], item['mac'] or __loc__(32022))
        for item in found
    ]
    selection = dialog.select(__loc__(32023), items)
    if selection < 0:
        return
    device = found[selection]

    name = dialog.input(
        __loc__(32024),
        defaultt=device['name'] or device['ip'],
        type=xbmcgui.INPUT_ALPHANUM,
    )
    if not name:
        return
    name = name.strip()
    if not name:
        return

    mac = dialog.input(
        __loc__(32027),
        defaultt=device['mac'],
        type=xbmcgui.INPUT_ALPHANUM,
    )
    if mac is None:
        return
    mac = mac.strip()
    if mac and not MAC_ADDRESS_PATTERN.match(mac):
        dialog.ok(__addonname__, __loc__(32028))
        return
    if not mac and not dialog.yesno(__addonname__, __loc__(32032)):
        return

    for number in range(1, 6):
        current_ip = __addon__.getSetting('ip{}'.format(number)).strip()
        current_mac = __addon__.getSetting('mac{}'.format(number)).strip()
        if current_ip == device['ip'] or (mac and _normalized_mac(current_mac) == _normalized_mac(mac)):
            dialog.ok(__addonname__, __loc__(32029))
            return

    slot = free_slots[0]
    summary = '{}\n{}\n{}'.format(name, device['ip'], mac or __loc__(32022))
    if not dialog.yesno(__addonname__, __loc__(32030).format(slot, summary)):
        return
    __addon__.setSetting('name{}'.format(slot), name)
    __addon__.setSetting('ip{}'.format(slot), device['ip'])
    __addon__.setSetting('mac{}'.format(slot), mac)
    dialog.ok(__addonname__, __loc__(32031).format(slot))


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
                    WINDOW.setProperty('{}.server{}'.format(PROPERTY_PREFIX, host_nr + 1), 'on')
                    self.host[host_nr][3] = icon_on
                    self.serveron += 1
                else:
                    WINDOW.setProperty('{}.server{}'.format(PROPERTY_PREFIX, host_nr + 1), 'off')
                    self.serveroff += 1
            else:
                WINDOW.clearProperty('{}.server{}'.format(PROPERTY_PREFIX, host_nr + 1))

            WINDOW.setProperty('{}.ip{}'.format(PROPERTY_PREFIX, host_nr + 1), self.host[host_nr][0])
            WINDOW.setProperty('{}.mac{}'.format(PROPERTY_PREFIX, host_nr + 1), self.host[host_nr][1])
            WINDOW.setProperty('{}.servername{}'.format(PROPERTY_PREFIX, host_nr + 1), self.host[host_nr][2])

        WINDOW.setProperty('{}.servercount'.format(PROPERTY_PREFIX), str(self.servercount))
        WINDOW.setProperty('{}.serveron'.format(PROPERTY_PREFIX), str(self.serveron))
        WINDOW.setProperty('{}.serveroff'.format(PROPERTY_PREFIX), str(self.serveroff))


if __name__ == '__main__':
    param = sys.argv[1] if len(sys.argv) > 1 else ''
    if param == 'scan':
        scan_network_and_add_device()
    else:
        hosts = Hosts()
        if param == 'status':
            exit(0)
        elif param[0:3] == 'wol':
            try:
                host_nr = int(param[3:]) - 1
            except ValueError:
                host_nr = -1
            if host_nr not in range(5):
                xbmc.log('Wrong WOL parameter: {}'.format(param), xbmc.LOGERROR)
                exit(1)
            xbmc.log('Send WOL packet to {} (MAC {})'.format(hosts.host[host_nr][2], hosts.host[host_nr][1]), xbmc.LOGINFO)
            wol(hosts.host[host_nr][1])
        elif param:
            xbmc.log('Wrong parameter: {}'.format(param), xbmc.LOGERROR)
        else:
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
