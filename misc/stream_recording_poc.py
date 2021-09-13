import requests, sys

URL = 'https://14543.live.streamtheworld.com/KMGLFMAAC.aac?pname=StandardPlayerV4&pversion=4.19.2-041&dist=triton-web&tdsdk=js-2.9&banners=300x250&sbmid=f9b251b5-dda4-402a-b67c-4c52e64b0dfb'
# URL = get_stream_url()

try:
    req = None
    req = requests.request('GET', URL, stream=True)

    counter = 0
    allTheBytes = b''
    for b in req.iter_content():
        allTheBytes += b
        counter += 1
        if counter > 145632:
            break
        

    with open('./misc/output/recorded.aac', 'wb') as f:
        f.write(allTheBytes)
finally:
    if req != None:
        req.close()
    pass