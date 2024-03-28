command = '''$headers = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
$headers.Add("product", "gpea010")
$headers.Add("companyid", "01")
$headers.Add("branchid", "00101001")
$headers.Add("Authorization", "Basic aW50ZWdyYWNhby5ncnM6aW50ZWdyYWNhb0BncnMxMjM=")

$response = Invoke-RestMethod 'https://protheus.funcionalmais.com:9134/rest/rh/v1/employeedatacontent' -Method 'GET' -Headers $headers
$response | ConvertTo-Json'''
import subprocess
subprocess.call(["powershell","/C",command])