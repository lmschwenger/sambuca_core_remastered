import os

from sambuca.core import DataFetcherFactory


aoi = "11.8,56.6,12.0,56.8"  # Anholt example
date = "2017-08-23"

s3_fetcher = DataFetcherFactory.create(fetcher_name="sentinel3")

results = s3_fetcher.fetch_data(aoi=aoi,
                                date=date
                                )

print("Files saved: ")
for key, val in results.items():
    print(f"{key}: {val}")