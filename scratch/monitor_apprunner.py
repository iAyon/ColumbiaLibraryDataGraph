import subprocess
import json
import time

SERVICE_ARN = "arn:aws:apprunner:us-east-1:682033467946:service/columbia-library-datagraph/ced9870fa80c4c08885b7673eb406d8c"

while True:
    try:
        res = subprocess.check_output(
            ["aws", "apprunner", "describe-service", "--service-arn", SERVICE_ARN, "--region", "us-east-1"],
            text=True
        )
        data = json.loads(res)
        status = data.get("Service", {}).get("Status")
        url = data.get("Service", {}).get("ServiceUrl")
        print(f"[{time.strftime('%H:%M:%S')}] AWS App Runner Status: {status}")
        
        if status in ["RUNNING", "CREATE_FAILED", "DELETED"]:
            print(f"DEPLOYMENT COMPLETE! Final Status: {status} | Service URL: https://{url}")
            break
    except Exception as e:
        print(f"Error checking status: {e}")
        
    time.sleep(15)
