import json
import cbor2
import requests
import os

url = "https://raw.githubusercontent.com/blawar/titledb/master/cnmts.json"
data = json.loads(requests.get(url).text.upper())

out = {}
for tid in data:
    if(tid[:13] + "000") not in out:
        out[tid[:13] + "000"] = {}
    for ver in data[tid]:
        if("BUILDID" in data[tid][ver]["CONTENTENTRIES"][0]):
            out[tid[:13] + "000"][data[tid][ver]["VERSION"]] = data[tid][ver]["CONTENTENTRIES"][0]["BUILDID"][:16]

path = "versions.json"
path_cbor = "versions.cbor"
change = False
try:
    with open(path, 'r') as read_file:
        old = json.load(read_file)
        if(json.dumps(old) != json.dumps(out)):
            print(path + " changed")
            change = True
except FileNotFoundError:
    print("File doesn't exist")
    change = True

if(change):
    with open(path, 'w') as json_file:
        json.dump(out, json_file, indent = 4)
    with open(path_cbor, 'wb') as cbor_file:
        json_out = json.dumps(out)
        cbor2.dump(json_out, cbor_file)
    print("Updated " + path)

dir_path = "versions/"
if not(os.path.exists(dir_path)):
    os.mkdir(dir_path)

for tid in out:
    path = dir_path + tid + ".json"
    change = False
    if(os.path.exists(path)):
        with open(path, 'r') as json_file:
            old = json.load(json_file)
        if(json.dumps(old) != json.dumps(tid)):
            change = True
    else:
        change = True
    if(change):
        with open(path, 'w') as json_file:
            json.dump(out[tid], json_file, indent = 4)
