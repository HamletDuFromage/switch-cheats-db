import json
import cbor2
import requests

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
    with open(path, 'w') as cbor_file:
        cbor2.dump(out, cbor_file)
    print("Updated " + path)
