import pandas as pd
import syft as sy



data_site = sy.orchestra.launch(name="DTU-MIDAS-AFMNanoskin", reset=False)

client = data_site.login(email="info@openmined.org", password="changethis")


cars_df = pd.read_csv("pysyft\Cars Datasets 2025.csv", encoding="windows-1252")

Cars_asset = sy.Asset(
    name="Our data on cars",
    data = cars_df,      # real data
    mock = cars_df.head(10)  # mock data is just first 10 entries
)

# Dataset creation
Cars_Dataset = sy.Dataset(
    name="Cars dataset",
    description="This is for testing",
    summary="This is for testing",
    citation="I made this on my own",
)

Cars_Dataset.add_asset(Cars_asset)

print(Cars_Dataset)

# Upload dataset

#client.upload_dataset(dataset=Cars_Dataset) # only upload once

input("press key to land datasite")
data_site.land()
