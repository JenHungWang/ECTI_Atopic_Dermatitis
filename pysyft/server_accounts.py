import syft as sy
import pandas as pd

data_site = sy.orchestra.launch(name="DTU-MIDAS-AFMNanoskin", reset=False)

client = data_site.login(email="s230642@dtu.dk", password="AskeIsTheAdmin")
print("Our users are: " , client.users)

#client.account.update(name="Aske, the Admin to rule them all", institution="DTU")

rachel_account_info = client.users.create(
    email="rachel@datascience.inst",
    name="Dr. Rachel Science",
    password="syftrocks",
    password_verify="syftrocks",
    institution="Data Science Institute",
    website="https://datascience_institute.research.data"
)


print("Our users are: " , client.users)


input("press key to land datasite")
data_site.land()
