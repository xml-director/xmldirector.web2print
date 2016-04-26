
import pprint
import json
import tempfile
import requests
import fs.zipfs
from requests.auth import HTTPBasicAuth


def verify_result(result):
    data_json = result.json()
    if 'error' in data_json:
        print result.url
        print data_json['error']
        raise RuntimeError()

base_url = 'http://localhost:12020/Plone'
user = 'admin'
password = 'admin'
all_headers = {'content-type': 'application/json',
               'accept': 'application/json'}
nojson_all_headers = {'accept': 'application/json'}


def send_request(method='GET', path='/@@API', data=None, files=None, headers={}, folder=None, url=None, qs=None, no_json=False, force_files=None, timeout=300):

    f = getattr(requests, method.lower())
    api_url = url if url else base_url
    if folder:
        api_url += folder
    api_url += '/{}'.format(path)
    if qs:
        api_url += qs
    if no_json:
        request_headers = nojson_all_headers.copy()
    else:
        request_headers = all_headers.copy()
    request_headers.update(headers)
    print method, api_url

    if files:
        zip_tmp = tempfile.mktemp(suffix='.zip')
        with fs.zipfs.ZipFS(zip_tmp, 'w') as handle:
            for fname in files:
                with open(fname, 'rb') as fp_in:
                    with handle.open(fname, 'wb') as fp_out:
                        fp_out.write(fp_in.read())
        data = json.dumps(
            dict(zip=open(zip_tmp, 'rb').read().encode('base64')))

    if data:
        result = f(
            api_url,
            auth=HTTPBasicAuth(user, password),
            headers=request_headers,
            files=force_files,
            timeout=timeout,
            data=data)
    else:
        result = f(
            api_url,
            auth=HTTPBasicAuth(user, password),
            files=force_files,
            timeout=timeout,
            headers=request_headers)
    print result
    return result


print '-' * 80
print 'CREATE'
result = send_request('PUT', 'xmldirector-create', folder='/folder')
verify_result(result)
print result
data = result.json()
id = data['id']
url = data['url']
print(id)
print (url)


print '-' * 80
print 'UPLOAD DOCX'
force_files = dict(zipfile=open('crex.zip', 'rb'))
print url
result = send_request('POST', 'xmldirector-store-zip',
                      force_files=force_files, url=url, no_json=True)
verify_result(result)
data = result.json()
pprint.pprint(data)

print '-' * 80
print 'GET_HASHES'
result = send_request('GET', 'xmldirector-hashes', url=url,
                      qs='?names:list=src/word/index.docx')
verify_result(result)
data = result.json()
pprint.pprint(data)

print '-' * 80
print 'GET_LIST_FULL'
result = send_request('GET', 'xmldirector-list-full', url=url)
verify_result(result)
data = result.json()
pprint.pprint(data)

print '-' * 80
print 'PUT CONVERT ASYNC'
data = dict(
    mapping=[
        ('src/(.*)', '$1')
    ])
result = send_request('POST', 'xmldirector-convert-async',
                      url=url, data=json.dumps(data))
print result.json()

for i in range(80):
    result = send_request('GET', 'xmldirector-convert-status', url=url)
    print result.json()
    import time
    time.sleep(5)


#result = send_request('POST', 'xmldirector-convert-async', url=url, data=json.dumps(data))
# print result.json()

# print '-' * 80
# print 'PUT CONVERT'
# data = dict(
# mapping=[
#('src/(.*)', '$1')
#])
#result = send_request('POST', 'xmldirector-convert', url=url, data=json.dumps(data))
# with open('out.zip', 'wb') as fp:
#    fp.write(result.content)

print '-' * 80
print 'GET_LIST_FULL'
result = send_request('GET', 'xmldirector-list-full', url=url)
verify_result(result)
data = result.json()
pprint.pprint(data)
