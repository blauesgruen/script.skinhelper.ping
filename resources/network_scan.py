# -*- coding: utf-8 -*-

"""Best-effort IPv4 host discovery using the local system's network tables."""

import ipaddress
import json
import os
import platform
import re
import socket
import subprocess
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait


MAX_SCAN_HOSTS = 4096
MAX_WORKERS = 64
MAC_PATTERN = re.compile(r'^(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}$', re.IGNORECASE)


def _run(command, timeout=5):
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=timeout,
        )
        return result.stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ''


def _usable_network(address, prefix, interface):
    try:
        interface_address = ipaddress.IPv4Interface('{}/{}'.format(address, prefix))
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        return None
    ip = interface_address.ip
    if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        return None
    return {
        'interface': interface,
        'address': str(ip),
        'network': interface_address.network,
    }


def _windows_networks():
    command = (
        "$ErrorActionPreference='Stop'; "
        "$up=Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
        "ForEach-Object {$_.InterfaceIndex}; "
        "Get-NetIPAddress -AddressFamily IPv4 | "
        "Where-Object {$_.AddressState -ne 'Duplicate' -and $up -contains $_.InterfaceIndex} | "
        "Select-Object IPAddress,PrefixLength,InterfaceAlias | "
        "ConvertTo-Json -Compress"
    )
    output = _run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], timeout=10)
    if not output:
        output = _run(['pwsh.exe', '-NoProfile', '-NonInteractive', '-Command', command], timeout=10)
    if not output:
        return []
    try:
        entries = json.loads(output)
    except (TypeError, ValueError):
        return []
    if isinstance(entries, dict):
        entries = [entries]
    networks = []
    for entry in entries:
        network = _usable_network(
            entry.get('IPAddress', ''),
            entry.get('PrefixLength', ''),
            entry.get('InterfaceAlias', ''),
        )
        if network:
            networks.append(network)
    return _unique_networks(networks)


def _posix_networks():
    system = platform.system().lower()
    networks = []
    if system == 'linux' or 'android' in sys.platform.lower():
        output = _run(['ip', '-o', '-4', 'addr', 'show'], timeout=5)
        for line in output.splitlines():
            match = re.match(r'^\d+:\s+(\S+)\s+.*?\binet\s+(\d+(?:\.\d+){3})/(\d+)', line)
            if match:
                network = _usable_network(match.group(2), match.group(3), match.group(1).rstrip(':'))
                if network:
                    networks.append(network)
        if not networks:
            networks.extend(_linux_route_networks())
    else:
        output = _run(['ifconfig', '-a'], timeout=5)
        interface = ''
        for line in output.splitlines():
            if line and not line[0].isspace() and ':' in line:
                interface = line.split(':', 1)[0].split()[0]
            match = re.search(r'\binet\s+(\d+(?:\.\d+){3}).*?\bnetmask\s+(0x[0-9a-fA-F]+|\d+(?:\.\d+){3})', line)
            if match:
                mask = match.group(2)
                try:
                    prefix = ipaddress.IPv4Network('0.0.0.0/{}'.format(mask)).prefixlen
                except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
                    try:
                        prefix = bin(int(mask, 16)).count('1')
                    except ValueError:
                        continue
                network = _usable_network(match.group(1), prefix, interface)
                if network:
                    networks.append(network)
    return _unique_networks(networks)


def _linux_route_networks():
    """Fallback for Linux-like systems without the `ip` executable."""
    networks = []
    try:
        with open('/proc/net/route', 'r') as routes:
            next(routes, None)
            for line in routes:
                fields = line.split()
                if len(fields) < 8:
                    continue
                interface, destination, _gateway, flags, _ref, _use, _metric, mask = fields[:8]
                if int(flags, 16) & 1 == 0 or int(destination, 16) == 0:
                    continue
                # /proc/net/route stores IPv4 values in native little-endian form.
                address = socket.inet_ntoa(bytes.fromhex(destination)[::-1])
                netmask = socket.inet_ntoa(bytes.fromhex(mask)[::-1])
                prefix = ipaddress.IPv4Network('0.0.0.0/{}'.format(netmask)).prefixlen
                probe_address = str(ipaddress.IPv4Address(address) + 1)
                local_address = _local_address_for_route(probe_address)
                if local_address:
                    network = _usable_network(local_address, prefix, interface)
                    if network:
                        networks.append(network)
    except (OSError, ValueError, StopIteration):
        return []
    return networks


def _local_address_for_route(destination):
    # A UDP route lookup reveals the source address selected by the kernel.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((destination, 9))
        address = sock.getsockname()[0]
        if address and not address.startswith('127.'):
            return address
    except OSError:
        pass
    finally:
        sock.close()
    return ''


def _unique_networks(networks):
    unique = {}
    for network in networks:
        key = (network['address'], str(network['network']))
        unique[key] = network
    return sorted(unique.values(), key=lambda item: (item['interface'].lower(), item['address']))


def get_networks():
    """Return IPv4 interface networks supported by the current OS."""
    if os.name == 'nt':
        return _windows_networks()
    return _posix_networks()


def host_addresses(network):
    """Return scan targets, excluding the Kodi host and network endpoints."""
    return [str(address) for address in network['network'].hosts() if str(address) != network['address']]


def _probe(address):
    count_flag = '-n' if os.name == 'nt' else '-c'
    command = ['ping', count_flag, '1', address]
    if os.name == 'nt':
        command = ['ping', '-n', '1', '-w', '800', address]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _mac(value):
    value = (value or '').strip().replace('-', ':').lower()
    return value if MAC_PATTERN.match(value) and value != '00:00:00:00:00:00' else ''


def _windows_neighbors():
    command = (
        "$ErrorActionPreference='Stop'; "
        "Get-NetNeighbor -AddressFamily IPv4 | "
        "Select-Object IPAddress,LinkLayerAddress | ConvertTo-Json -Compress"
    )
    output = _run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], timeout=10)
    if not output:
        output = _run(['pwsh.exe', '-NoProfile', '-NonInteractive', '-Command', command], timeout=10)
    try:
        entries = json.loads(output) if output else []
    except (TypeError, ValueError):
        return {}
    if isinstance(entries, dict):
        entries = [entries]
    return {entry.get('IPAddress', ''): _mac(entry.get('LinkLayerAddress', '')) for entry in entries}


def _posix_neighbors():
    neighbors = {}
    try:
        with open('/proc/net/arp', 'r') as arp_table:
            next(arp_table, None)
            for line in arp_table:
                fields = line.split()
                if len(fields) >= 4 and int(fields[2], 0) != 0:
                    address, mac = fields[0], _mac(fields[3])
                    if mac:
                        neighbors[address] = mac
    except (OSError, ValueError):
        pass
    if neighbors:
        return neighbors
    output = _run(['arp', '-an'], timeout=5)
    for line in output.splitlines():
        match = re.search(r'\((\d+(?:\.\d+){3})\)\s+at\s+([0-9a-fA-F:-]{17})', line)
        if match:
            mac = _mac(match.group(2))
            if mac:
                neighbors[match.group(1)] = mac
    return neighbors


def get_neighbors():
    return _windows_neighbors() if os.name == 'nt' else _posix_neighbors()


def _hostname(address):
    try:
        name = socket.gethostbyaddr(address)[0].strip().rstrip('.')
        return name or address
    except (OSError, socket.herror, socket.gaierror):
        return address


def scan_network(network, progress_callback, cancel_callback):
    """Probe one bounded IPv4 network and return discovered IP/MAC/name records."""
    addresses = host_addresses(network)
    if len(addresses) > MAX_SCAN_HOSTS:
        raise ValueError('network_too_large')
    if not addresses:
        return []

    responding = set()
    executor = ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(addresses)))
    pending = {executor.submit(_probe, address): address for address in addresses}
    completed = 0
    canceled = False
    try:
        while pending:
            if cancel_callback():
                canceled = True
                break
            done, _ = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
            for future in done:
                address = pending.pop(future)
                if future.result():
                    responding.add(address)
                completed += 1
            progress_callback(completed, len(addresses))
    finally:
        if canceled:
            for future in pending:
                future.cancel()
        executor.shutdown(wait=not canceled)
    if canceled:
        return None

    neighbors = get_neighbors()
    discovered = set(responding)
    discovered.update(address for address in neighbors if address in network['network'])
    records = []
    for address in sorted(discovered, key=lambda value: tuple(int(part) for part in value.split('.'))):
        records.append({
            'ip': address,
            'mac': neighbors.get(address, ''),
            'name': _hostname(address),
        })
    return records
