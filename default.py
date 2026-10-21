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
DEVICE_SLOT_COUNT = 10


def wol(mac):
    if not mac or not MAC_ADDRESS_PATTERN.match(mac):
        xbmc.log('[script.skinhelper.ping] WOL: keine gültige MAC-Adresse konfiguriert', xbmc.LOGWARNING)
        return
    normalized_mac = mac.replace('-', ':').upper()
    xbmc.executebuiltin("WakeOnLan({})".format(normalized_mac))


def ping(current_ip_address, timeout=5):
    count = 'n' if platform.system().lower() == 'windows' else 'c'
    process_options = {}
    if os.name == 'nt':
        process_options['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    try:
        subprocess.run(
            ['ping', '-{}'.format(count), '1', current_ip_address],
            check=True,
            timeout=timeout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **process_options
        )
        return True
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        xbmc.log('Ping returns an error: {}'.format(e), xbmc.LOGERROR)
        return False


def _normalized_mac(mac):
    return (mac or '').replace('-', ':').replace(':', '').lower()


def _free_device_slots():
    return [
        number for number in range(1, DEVICE_SLOT_COUNT + 1)
        if not any(__addon__.getSetting('{}{}'.format(key, number)).strip() for key in ('ip', 'mac', 'name'))
    ]


def _device_is_configured(device):
    device_mac = _normalized_mac(device.get('mac', ''))
    for number in range(1, DEVICE_SLOT_COUNT + 1):
        current_ip = __addon__.getSetting('ip{}'.format(number)).strip()
        current_mac = _normalized_mac(__addon__.getSetting('mac{}'.format(number)))
        if current_ip == device['ip'] or (device_mac and current_mac == device_mac):
            return True
    return False


def remove_device(slot):
    dialog = xbmcgui.Dialog()
    name = __addon__.getSetting('name{}'.format(slot)).strip()
    ip = __addon__.getSetting('ip{}'.format(slot)).strip()
    mac = __addon__.getSetting('mac{}'.format(slot)).strip()
    if not any((name, ip, mac)):
        return

    description = '{}\n{}'.format(name or __loc__(32044).format(slot), ip)
    if not dialog.yesno(__addonname__, __loc__(32043).format(description)):
        return

    for key in ('name', 'ip', 'mac'):
        __addon__.setSetting('{}{}'.format(key, slot), '')

    # Clear this slot immediately and refresh totals from the remaining cached
    # statuses without pinging every configured device again.
    WINDOW.clearProperty('{}.server{}'.format(PROPERTY_PREFIX, slot))
    for key in ('servername', 'ip', 'mac'):
        WINDOW.setProperty('{}.{}{}'.format(PROPERTY_PREFIX, key, slot), '')

    configured = online = offline = 0
    for number in range(1, DEVICE_SLOT_COUNT + 1):
        if not __addon__.getSetting('ip{}'.format(number)).strip():
            continue
        configured += 1
        status = WINDOW.getProperty('{}.server{}'.format(PROPERTY_PREFIX, number))
        if status == 'on':
            online += 1
        elif status == 'off':
            offline += 1

    WINDOW.setProperty('{}.servercount'.format(PROPERTY_PREFIX), str(configured))
    WINDOW.setProperty('{}.serveron'.format(PROPERTY_PREFIX), str(online))
    WINDOW.setProperty('{}.serveroff'.format(PROPERTY_PREFIX), str(offline))
    dialog.notification(__addonname__, __loc__(32045).format(slot), __icon__)


def scan_network_and_add_device():
    dialog = xbmcgui.Dialog()
    if not _free_device_slots():
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
        # Reserve the last 10% for reading the neighbor table and bounded
        # reverse-DNS lookups after all ping probes have completed.
        percent = int(completed * 90 / total) if total else 90
        progress.update(percent, __loc__(32019).format(completed, total))

    try:
        found = network_scan.scan_network(
            selected_network,
            update_progress,
            progress.iscanceled,
        )
        if found is not None:
            progress.update(100, __loc__(32019).format(host_count, host_count))
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

    available = [device for device in found if not _device_is_configured(device)]
    if not available:
        dialog.ok(__addonname__, __loc__(32035))
        return

    while available:
        free_slots = _free_device_slots()
        if not free_slots:
            dialog.ok(__addonname__, __loc__(32025))
            return

        items = [
            '{} \u2014 {} \u2014 {}'.format(item['name'], item['ip'], item['mac'] or __loc__(32022))
            for item in available
        ]
        selection = dialog.select(__loc__(32023), items)
        if selection < 0:
            return
        device = available[selection]

        name = dialog.input(
            __loc__(32024),
            defaultt=device['name'] or device['ip'],
            type=xbmcgui.INPUT_ALPHANUM,
        )
        if not name or not name.strip():
            continue
        name = name.strip()

        mac = device.get('mac', '') or ''
        if _device_is_configured({'ip': device['ip'], 'mac': mac}):
            dialog.ok(__addonname__, __loc__(32029))
            continue

        free_slots = _free_device_slots()
        slot_labels = [__loc__(32034).format(number) for number in free_slots]
        slot_selection = dialog.select(__loc__(32033), slot_labels)
        if slot_selection < 0:
            continue
        slot = free_slots[slot_selection]

        summary = '{}\n{}'.format(name, device['ip'])
        if not dialog.yesno(__addonname__, __loc__(32030).format(slot, summary)):
            continue
        __addon__.setSetting('name{}'.format(slot), name)
        __addon__.setSetting('ip{}'.format(slot), device['ip'])
        __addon__.setSetting('mac{}'.format(slot), mac)
        available.remove(device)
        dialog.ok(__addonname__, __loc__(32031).format(slot))


class Hosts:

    def __init__(self):
        self.servercount = 0
        self.serveron = 0
        self.serveroff = 0
        self.host = list()

        for host_nr in range(DEVICE_SLOT_COUNT):
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
    elif param.startswith('remove'):
        try:
            slot = int(param[6:])
        except ValueError:
            slot = 0
        if slot not in range(1, DEVICE_SLOT_COUNT + 1):
            xbmc.log('Wrong remove parameter: {}'.format(param), xbmc.LOGERROR)
            exit(1)
        remove_device(slot)
    else:
        hosts = Hosts()
        if param == 'status':
            exit(0)
        elif param[0:3] == 'wol':
            try:
                host_nr = int(param[3:]) - 1
            except ValueError:
                host_nr = -1
            if host_nr not in range(DEVICE_SLOT_COUNT):
                xbmc.log('Wrong WOL parameter: {}'.format(param), xbmc.LOGERROR)
                exit(1)
            xbmc.log('Send WOL packet to {} (MAC {})'.format(hosts.host[host_nr][2], hosts.host[host_nr][1]), xbmc.LOGINFO)
            wol(hosts.host[host_nr][1])
        elif param:
            xbmc.log('Wrong parameter: {}'.format(param), xbmc.LOGERROR)
        else:
            host_list = list()
            for host_nr in range(DEVICE_SLOT_COUNT):
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
