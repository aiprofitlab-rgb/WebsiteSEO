import json

def parse_commit_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Find JSON start
    json_start = content.find('{"sha":')
    if json_start == -1:
        print("JSON not found in file", filepath)
        return
    try:
        data = json.loads(content[json_start:])
        print("Commit message:", data["commit"]["message"])
        print("Files:")
        for file in data.get("files", []):
            print(f"- {file['filename']} ({file['status']})")
    except Exception as e:
        print("Error parsing JSON:", e)

print("=== Commit 2c0dd18 ===")
parse_commit_file("/Users/nahid/.gemini/antigravity-ide/brain/9a5a018b-1251-4397-9a51-cb3a841ecfcb/.system_generated/steps/119/content.md")
