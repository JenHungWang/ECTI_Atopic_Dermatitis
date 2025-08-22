import syft as sy
import pandas as pd

data_site = sy.orchestra.launch(name="DTU-MIDAS-AFMNanoskin", reset=False)

client = data_site.login(email="s230642@dtu.dk", password="AskeIsTheAdmin")

print(client.datasets)

input("press key to land datasite")
data_site.land()
