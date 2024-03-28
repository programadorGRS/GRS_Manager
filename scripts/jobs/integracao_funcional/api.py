import http.client

conn = http.client.HTTPSConnection("protheus.funcionalmais.com", 9134)
payload = ''
headers = {
  'product': 'protheus',
  'companyid': '01',
  
  'branchid': '00101001'
}
conn.request("GET", "/rest/FHTGPW06", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))