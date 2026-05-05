import os

files_to_check = [
    'public_html/blog/en/2026-05-05-omantel-otech-sovereign-cloud.html',
    'public_html/blog/ar/2026-05-05-omantel-otech-sovereign-cloud.html'
]

old_iframe_en = '<iframe class="absolute top-0 left-0 w-full h-full" src="https://www.youtube.com/embed/Xq5N9D2VfGk" title="Omantel Otech Sovereign Cloud Launch" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'

old_iframe_ar = '<iframe class="absolute top-0 left-0 w-full h-full" src="https://www.youtube.com/embed/Xq5N9D2VfGk" title="إطلاق سحابة عمانتل أوتك السيادية" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'

new_iframe_en = '<iframe class="absolute top-0 left-0 w-full h-full" src="https://www.youtube.com/embed/xB8RxaQvqD0" srcdoc="<style>*{padding:0;margin:0;overflow:hidden}html,body{height:100%;background:#000}img,span{position:absolute;width:100%;top:0;bottom:0;margin:auto}span{height:1.5em;text-align:center;font:48px/1.5 sans-serif;color:white;text-shadow:0 0 0.5em black}</style><a href=https://www.youtube.com/embed/xB8RxaQvqD0?autoplay=1><img src=https://img.youtube.com/vi/xB8RxaQvqD0/hqdefault.jpg alt=\'Omantel Otech Sovereign Cloud Launch\'><span>▶</span></a>" title="Omantel Otech Sovereign Cloud Launch" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>'

new_iframe_ar = '<iframe class="absolute top-0 left-0 w-full h-full" src="https://www.youtube.com/embed/xB8RxaQvqD0" srcdoc="<style>*{padding:0;margin:0;overflow:hidden}html,body{height:100%;background:#000}img,span{position:absolute;width:100%;top:0;bottom:0;margin:auto}span{height:1.5em;text-align:center;font:48px/1.5 sans-serif;color:white;text-shadow:0 0 0.5em black}</style><a href=https://www.youtube.com/embed/xB8RxaQvqD0?autoplay=1><img src=https://img.youtube.com/vi/xB8RxaQvqD0/hqdefault.jpg alt=\'إطلاق سحابة عمانتل أوتك السيادية\'><span>▶</span></a>" title="إطلاق سحابة عمانتل أوتك السيادية" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>'


for file_path in files_to_check:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'en/' in file_path:
            content = content.replace(old_iframe_en, new_iframe_en)
        else:
            content = content.replace(old_iframe_ar, new_iframe_ar)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated iframe in {file_path}")
