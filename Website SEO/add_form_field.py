import os
import re
import glob

en_addition = '''
                    <label>How did you hear about us?</label>
                    <div class="checkbox-group">
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

ar_addition = '''<label>كيف سمعت عنا؟</label><div class="checkbox-group"><label class="checkbox-item"><input type="checkbox" name="source" value="LinkedIn"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>لينكد إن (LinkedIn)</label><label class="checkbox-item"><input type="checkbox" name="source" value="YouTube"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>يوتيوب (YouTube)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Google Search"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>بحث جوجل</label><label class="checkbox-item"><input type="checkbox" name="source" value="Chat GPT"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>شات جي بي تي (Chat GPT)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Gemini"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>جيميني (Gemini)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Claude"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>كلود (Claude)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Perplexity"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>بيربلكسيتي (Perplexity)</label><label class="checkbox-item"><input type="checkbox" name="source" value="Word of mouth"><span class="checkmark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7"/></svg></span>عن طريق المعارف</label></div><label for="otherSource">أخرى (يرجى التحديد)</label><input type="text" id="otherSource" name="otherSource">'''

en_target = r'(<label for="keyQuestion">Must-Ask Question for Our Call\? <span class="required">\*</span></label>\s*<input type="text" id="keyQuestion" name="keyQuestion" required>)'
ar_target = r'(<label for="keyQuestion">السؤال الذي يجب طرحه في مكالمتنا\؟ <span class="required">\*</span></label>\s*<input type="text" id="keyQuestion" name="keyQuestion" required>)'

files = glob.glob('public_html/**/*.html', recursive=True)

modified_count = 0
for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    if "Must-Ask Question for Our Call?" in content and "How did you hear about us?" not in content:
        content = re.sub(en_target, en_addition + r'\1', content)
        
    if "السؤال الذي يجب طرحه في مكالمتنا" in content and "كيف سمعت عنا؟" not in content:
        content = re.sub(ar_target, ar_addition + r'\1', content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_count += 1
        print(f"Modified {file_path}")

print(f"Total files modified: {modified_count}")
