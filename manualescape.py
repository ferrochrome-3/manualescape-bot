import os
import sys
import uuid
import requests
import device_management_backend_pb2 as proto

serial_number = input("").strip()
oauth_code = input("").strip()

response = requests.post(
    "https://www.googleapis.com/oauth2/v4/token",
    data={
        "code": oauth_code,
        "client_id": "77185425430.apps.googleusercontent.com",
        "client_secret": "OTJgUOQcT7lO7GsGZq2G4IlT",
        "grant_type": "authorization_code",
    },
)

if not response.ok:
    sys.exit("oauth exchange failed: invalid or expired oauth code, please generate a new one")

refresh_token = response.json()["refresh_token"]

response = requests.post(
    "https://www.googleapis.com/oauth2/v4/token",
    data={
        "client_id": "77185425430.apps.googleusercontent.com",
        "client_secret": "OTJgUOQcT7lO7GsGZq2G4IlT",
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://www.googleapis.com/auth/chromeosdevicemanagement",
    },
)

response.raise_for_status()
oauth_token = response.json()["access_token"]

device_id = str(uuid.uuid4())

register_request = proto.DeviceRegisterRequest()
register_request.type = proto.DeviceRegisterRequest.DEVICE
register_request.machine_id = serial_number

request = proto.DeviceManagementRequest()
request.register_request.CopyFrom(register_request)

response = requests.post(
    f"https://m.google.com/devicemanagement/data/api?apptype=Chrome&deviceid={device_id}&devicetype=2&oauth_token={oauth_token}&request=register",
    headers={
        "Content-Type": "application/protobuf",
    },
    data=request.SerializeToString(),
)

data = proto.DeviceManagementResponse()
data.ParseFromString(response.content)

if data.error_message:
    sys.exit(f"registration error: {data.error_message}")

dmtoken = data.register_response.device_management_token

policy_fetch_request = proto.PolicyFetchRequest()
policy_fetch_request.policy_type = "google/chromeos/device"

state_key_update_request = proto.DeviceStateKeyUpdateRequest()
state_key_update_request.server_backed_state_keys.extend(os.urandom(32) for _ in range(5))

request = proto.DeviceManagementRequest()
request.policy_request.requests.append(policy_fetch_request)
request.device_state_key_update_request.CopyFrom(state_key_update_request)

response = requests.post(
    f"https://m.google.com/devicemanagement/data/api?apptype=Chrome&deviceid={device_id}&devicetype=2&request=policy",
    headers={
        "Authorization": f"GoogleDMToken token={dmtoken}",
        "Content-Type": "application/protobuf",
    },
    data=request.SerializeToString(),
)

data = proto.DeviceManagementResponse()
data.ParseFromString(response.content)

if data.error_message:
    sys.exit(f"policy fetch error: {data.error_message}")

print(f"Successfully unenrolled device {serial_number}!")
