#requires -RunAsAdministrator
# Earshot offline restore (01 §3.11). Removes the block rules created by
# cut-internet.ps1 so the laptop is never left cut off.

# RESTORE
Remove-NetFirewallRule -Group "EarshotOffline"
