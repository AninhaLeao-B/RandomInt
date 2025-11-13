
Start-Process powershell -ArgumentList "-Command `$env:SERVER_ID='Server1'; `$env:SERVER_PORT='5001'; python server.py"
Start-Process powershell -ArgumentList "-Command `$env:SERVER_ID='Server2'; `$env:SERVER_PORT='5002'; python server.py"
Start-Process powershell -ArgumentList "-Command `$env:SERVER_ID='Server3'; `$env:SERVER_PORT='5003'; python server.py"
Start-Process powershell -ArgumentList "-Command python load_balancer.py"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-Command python client.py"