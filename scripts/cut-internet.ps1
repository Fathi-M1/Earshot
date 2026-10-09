#requires -RunAsAdministrator
# Earshot offline cut (01 §3.11). Blocks every non-private IPv4 destination,
# all global IPv6, and DNS via the hotspot gateway, while leaving the hotspot
# LAN (incl. 172.16.0.0/12) reachable so the iPhone still loads the phone page.
# Block rules beat allow rules in Windows Firewall.

# CUT: block every non-private IPv4 destination, all global IPv6, and DNS via the hotspot
$v4 = "1.0.0.0-9.255.255.255","11.0.0.0-126.255.255.255","128.0.0.0-169.253.255.255","169.255.0.0-172.15.255.255","172.32.0.0-192.167.255.255","192.169.0.0-223.255.255.255"
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block internet IPv4" -Direction Outbound -Action Block -RemoteAddress $v4 -Profile Any
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block internet IPv6" -Direction Outbound -Action Block -RemoteAddress "2000::-3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff" -Profile Any
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block DNS via hotspot UDP" -Direction Outbound -Action Block -Protocol UDP -RemotePort 53 -RemoteAddress "172.20.10.1" -Profile Any
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block DNS via hotspot TCP" -Direction Outbound -Action Block -Protocol TCP -RemotePort 53 -RemoteAddress "172.20.10.1" -Profile Any
Get-NetFirewallProfile | Select Name, Enabled          # all must be True, or rules do nothing
Test-NetConnection 1.1.1.1 -Port 443                    # expect TcpTestSucceeded : False
