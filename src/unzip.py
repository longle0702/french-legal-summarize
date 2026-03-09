import tarfile
import os

file = "Freemium_cass_global_20250713-140000.tar.gz"
extract = "."

with tarfile.open(file, "r:gz") as tar:
    tar.extractall(path=extract)