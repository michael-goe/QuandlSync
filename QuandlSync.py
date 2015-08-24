# QuandlSync: Keep up-to-date copies of Quandl collections. 

import Quandl
import pandas
import urllib.request
import concurrent.futures
import time
import json
import os
import os.path

# Constants
metadata_pattern = "https://www.quandl.com/api/v2/datasets.csv?query=*&source_code={0}&per_page=300&page={1}&auth_token={2}"

# Settings
collections = []
auth_token = ""


def download_metadata(collection):
    """
    Downloads given collection's metadata. Overwrites old state in case it has
    been downloaded before. First fetch otherwise.
    """
    print("Downloading metadata for {0}".format(collection))
    collection_path = os.path.join("collections/{}".format(collection))
    if not os.path.exists("./collections"):
        os.makedirs("collections")
    if not os.path.exists(collection_path):
        os.makedirs(collection_path)
    
    page_count = 1
    pages = list()
    eof_reached = False
    while not eof_reached:
        url = metadata_pattern.format(collection, page_count, auth_token)
        current_page = urllib.request.urlopen(url).read().decode("UTF-8")
        pages.append(current_page)
        if current_page != "":
            page_count += 1
        else:
            eof_reached = True
	
    metadata = ''.join(pages)
    metadata_file = open(os.path.join(collection_path, "metadata.csv"), "w")
    metadata_file.write(metadata)
    metadata_file.close()
    
def quandl_download(ds_code, ds_path):
    """
    Executes Quandl API call for downloading whole dataset and saves it to given path.
    """
    print("Downloading dataset: {0}".format(ds_code))
    ds_data = Quandl.get(ds_code)
    ds_data.to_csv(ds_path)
    
def quandl_update(ds_code, ds_path, trim_start):
    """
    TODO
    """
    pass
    
def download_datasets(collection):
    """
    Downloads datasets of a given collection. New files are fetched in full,
    existing files are appended only the new entries since last update.
    """
    print("Downloading datasets for {0}".format(collection))
    collection_path = os.path.join("collections/{}".format(collection))
    collection_metadata = pandas.read_csv(os.path.join(collection_path, "metadata.csv"))
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    # TODO: DUPLICATES
    # Iterate over datasets in collection
    for idx, row in collection_metadata.iterrows():
        #print("Dataset {0} last updated at {1}".format(row[0], row[5]))
        ds_code = row[0]
        ds_name = ds_code.split("/")[1]
        ds_path = os.path.join(collection_path, ds_name+".csv")
        
        if not os.path.exists(ds_path):
            executor.submit(quandl_download, ds_code, ds_path)
        else:
            ds_data = pandas.read_csv(ds_path)
            last_update = pandas.Timestamp(ds_data.iloc[-1][0])
            last_change = pandas.Timestamp(row[3])
            #print("Last update {0}: {1}, last change: {2}".format(ds_name, last_update, last_change))
            if last_change > last_update:
                ds_diff = Quandl.get(ds_code, trim_start=last_update+pandas.DateOffset(days=1))
                if not ds_diff.empty:
                    print("Updating dataset: {0}".format(ds_code))
                    ds_file = open(ds_path, "a")
                    ds_file.write(ds_diff.to_csv(header=False, index_names=False))
                    ds_file.close()

def read_settings():
    global auth_token
    global collections
    settings = json.load(open("settings.json", "r"))
    auth_token = settings["api_key"]
    collections = settings["collections"]
    
if __name__ == "__main__":
    read_settings()
    for collection in collections:
        download_metadata(collection)
        download_datasets(collection)

