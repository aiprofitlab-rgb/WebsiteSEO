import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import ssl

def submit_to_indexnow():
    sitemap_file = 'public_html/sitemap.xml'
    host = 'aiprofitlab.io'
    key = 'e536bc90942243bf96f50cbb57df9c2f'
    key_location = f'https://{host}/{key}.txt'

    print(f"Reading URLs from {sitemap_file}...")
    
    try:
        tree = ET.parse(sitemap_file)
        root = tree.getroot()
        
        # Namespace for sitemaps
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        urls = []
        for loc in root.findall('.//sm:loc', ns):
            if loc.text:
                urls.append(loc.text)
                
        print(f"Found {len(urls)} URLs.")
        
        if not urls:
            print("No URLs found to submit.")
            return

        # Prepare IndexNow payload
        payload = {
            "host": host,
            "key": key,
            "keyLocation": key_location,
            "urlList": urls
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            'https://api.indexnow.org/indexnow',
            data=data,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        
        # Ignore SSL verification if needed, though standard should work
        ctx = ssl.create_default_context()
        
        print("Submitting to IndexNow API...")
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status == 200 or response.status == 202:
                print("Successfully submitted URLs to IndexNow!")
            else:
                print(f"Failed with status code: {response.status}")
                print(response.read().decode('utf-8'))
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    submit_to_indexnow()
