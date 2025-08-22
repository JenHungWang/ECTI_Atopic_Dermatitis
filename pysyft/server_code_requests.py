import syft as sy
import pandas as pd

data_site = sy.orchestra.launch(name="DTU-MIDAS-AFMNanoskin", reset=False)

client = data_site.login(email="s230642@dtu.dk", password="AskeIsTheAdmin")

print(client.projects[0])

request = client.requests[0]

print(request.code.raw_code)

print(request.status)

request.approve()

print(request.status)

data_site.land()