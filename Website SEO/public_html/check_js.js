const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Basic regex to extract script tags
const extractScripts = (html) => {
    const scripts = [];
    const regex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
    let match;
    while ((match = regex.exec(html)) !== null) {
        if (match[1].trim() !== '') {
            scripts.push({
                content: match[1],
                start: match.index
            });
        }
    }
    return scripts;
};

// We can just use acorn or basic eval to check syntax
// Since acorn isn't definitely installed, we can just spawn a node process with the script content to check syntax
const { execSync } = require('child_process');

const files = glob.sync('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html');
let hasErrors = false;

files.forEach(file => {
    const content = fs.readFileSync(file, 'utf8');
    const scripts = extractScripts(content);
    
    scripts.forEach((script, idx) => {
        const tmpFile = path.join(__dirname, 'tmp_script.js');
        // Wrap in an async function if it uses await outside
        let jsCode = script.content;
        fs.writeFileSync(tmpFile, jsCode);
        try {
            execSync(`node -c tmp_script.js`, { stdio: 'ignore' });
        } catch (e) {
            // Check if error is just about 'await' being a reserved word outside async
            if (e.message && e.message.includes("await")) {
                fs.writeFileSync(tmpFile, `(async () => { ${jsCode} })();`);
                try {
                     execSync(`node -c tmp_script.js`, { stdio: 'ignore' });
                } catch (e2) {
                     console.log(`Syntax Error in ${file} script #${idx + 1}`);
                     hasErrors = true;
                }
            } else {
                console.log(`Syntax Error in ${file} script #${idx + 1}`);
                hasErrors = true;
            }
        }
    });
});
if (!hasErrors) console.log("All scripts passed syntax check!");
