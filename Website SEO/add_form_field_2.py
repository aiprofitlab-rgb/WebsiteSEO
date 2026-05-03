import os
import re
import glob

en_addition = '''
                    <label style="margin-top: 1rem; display: block; font-weight: bold;">How did you hear about us?</label>
                    <div class="checkbox-group" style="margin-bottom: 1rem;">
                        <label class="checkbox-item"><input type="checkbox" name="source" value="LinkedIn"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>LinkedIn</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="YouTube"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>YouTube</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="Google Search"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>Google Search</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="Chat GPT"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>Chat GPT</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="Gemini"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>Gemini</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="Claude"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>Claude</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="Perplexity"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>Perplexity</label>
                        <label class="checkbox-item"><input type="checkbox" name="source" value="Word of mouth"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>Word of mouth</label>
                    </div>
                    <label for="otherSource">Others (Please specify)</label>
                    <input type="text" id="otherSource" name="otherSource">
'''

ar_addition = '''<label style="margin-top: 1rem; display: block; font-weight: bold;">كيف سمعت عنا؟</label><div class="checkbox-group" style="margin-bottom: 1rem;"><label class="checkbox-item"><input type="checkbox" name="source" value="LinkedIn"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>لينكد إن (LinkedIn)</label><label class="checkbox-item"><input type="checkbox" name="source" value="YouTube"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>يوتيوب (YouTube)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Google Search"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>بحث جوجل</label><label class="checkbox-item"><input type="checkbox" name="source" value="Chat GPT"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>شات جي بي تي (Chat GPT)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Gemini"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>جيميني (Gemini)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Claude"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>كلود (Claude)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Perplexity"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>بيربلكسيتي (Perplexity)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Word of mouth"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>عن طريق المعارف</label></div><label for="otherSource">أخرى (يرجى التحديد)</label><input type="text" id="otherSource" name="otherSource">'''

files = glob.glob('public_html/**/*.html', recursive=True)

modified_count = 0
for file_path in files:
    if "blog/" in file_path:
        continue # skip blog articles just in case
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # Check if we should modify
    if 'id="keyQuestion"' in content:
        # Check language
        if 'dir="rtl"' in content or 'lang="ar"' in content or "كيف سمعت عنا" in content or 'التالي' in content:
            # Arabic
            if "كيف سمعت عنا" not in content:
                # Find the keyQuestion input
                pattern = r'(<input[^>]*id="keyQuestion"[^>]*>)'
                content = re.sub(pattern, r'\1\n' + ar_addition, content)
        else:
            # English
            if "How did you hear about us" not in content:
                pattern = r'(<input[^>]*id="keyQuestion"[^>]*>)'
                content = re.sub(pattern, r'\1\n' + en_addition, content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_count += 1
        print(f"Modified {file_path}")

print(f"Total files modified: {modified_count}")
