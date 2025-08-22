import syft as sy

data_site = sy.orchestra.launch(name="DTU-MIDAS-AFMNanoskin", reset=False)

client = data_site.login(email="rachel@datascience.inst", password="syftrocks")

print(client.datasets)

Cars_dataset = client.datasets["Cars dataset"]

print(Cars_dataset)

asset = Cars_dataset.assets["Our data on cars"]

def MostCommonBrand(data):
    return data["Company Names"].value_counts().idxmax()

print("Most common brand in mock")
print(MostCommonBrand(asset.mock))

""""
remote_user_code = sy.syft_function_single_use(data=asset)(MostCommonBrand)

MostCommonBrand_project = client.create_project(
    name="Wonder what the most common brand is?",
    description="this is a test",
    user_email_address="rachel@datascience.inst"
)


code_request = MostCommonBrand_project.create_code_request(remote_user_code,client)
"""
print(client.requests[0 ].status)

print("Most common brand FOR REAL")
result = client.code.MostCommonBrand(data=asset).get()
print(result)
input("press key to land datasite")
data_site.land()
