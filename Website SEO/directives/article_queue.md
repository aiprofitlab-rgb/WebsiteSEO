# Daily Article Publishing Queue

This queue tracks remaining articles to be generated, illustrated, and published to AI Profit Lab.

| # | Cluster | English Title | Arabic Title | Status | Published Date | Live URL |
|---|---|---|---|---|---|---|
| 60 | Cluster 6: Technical Implementation & Integrations | Measuring AI Agent Performance: Latency, Accuracy, and User Satisfaction Metrics | قياس أداء وكلاء الذكاء الاصطناعي: السرعة، الدقة، ومعدلات رضا المستخدم | Repair | 2026-10-12 | [2026-10-12-measuring-ai-agent-performance-latency-accuracy-and-user-sat](https://aiprofitlab.io/blog/en/2026-10-12-measuring-ai-agent-performance-latency-accuracy-and-user-sat/) |
| 59 | Cluster 6: Technical Implementation & Integrations | Building Fail-Safe AI Workflows for High-Volume E-Commerce Flash Sales | بناء سير عمل مؤتمت ومضمون للتجارة الإلكترونية أثناء فترة العروض الكبرى | Repair | 2026-10-11 | [2026-10-11-building-fail-safe-ai-workflows-for-high-volume-e-commerce-f](https://aiprofitlab.io/blog/en/2026-10-11-building-fail-safe-ai-workflows-for-high-volume-e-commerce-f/) |
| 29 | Cluster 3: Autonomous AI Agents | Building Custom Multi-Agent AI Swarms for Market Research in the Gulf | بناء شبكات وكلاء الذكاء الاصطناعي المخصصة لدراسات السوق في الخليج | Repair | 2026-10-03 | [2026-10-03-building-custom-multi-agent-ai-swarms-market-research-gulf](https://aiprofitlab.io/blog/en/2026-10-03-building-custom-multi-agent-ai-swarms-market-research-gulf/) |
| 30 | Cluster 3: Autonomous AI Agents | The ROI of Autonomous AI Agents: Calculating Cost Savings for Omani Businesses | عائد الاستثمار من وكلاء الذكاء الاصطناعي: حساب توفير التكاليف للشركات العمانية | Repair | 2026-10-04 | [2026-10-04-the-roi-of-autonomous-ai-agents-calculating-cost-savings-for](https://aiprofitlab.io/blog/en/2026-10-04-the-roi-of-autonomous-ai-agents-calculating-cost-savings-for/) |
| 39 | Cluster 4: Industry-Specific AI Applications | Hospitality AI in Muscat: Automating Room Service, Check-ins, and Concierge | الذكاء الاصطناعي في قطاع الضيافة بمسقط: أتمتة خدمة الغرف وتسجيل الوصول والكونسيرج | Repair | 2026-10-05 | [2026-10-05-hospitality-ai-in-muscat-automating-room-service-check-ins-a](https://aiprofitlab.io/blog/en/2026-10-05-hospitality-ai-in-muscat-automating-room-service-check-ins-a/) |
| 40 | Cluster 4: Industry-Specific AI Applications | Supercharging Omani Digital Marketing Agencies with Automated Content Pipelines | تمكين وكالات التسويق الرقمي العمانية باستخدام خطوط إنتاج المحتوى المؤتمتة | Repair | 2026-10-06 | [2026-10-06-supercharging-omani-digital-marketing-agencies-with-automate](https://aiprofitlab.io/blog/en/2026-10-06-supercharging-omani-digital-marketing-agencies-with-automate/) |
| 48 | Cluster 5: Executive Strategy, Vision 2040 & ROI | Upskilling Your Omani Workforce for the AI Era: Change Management Essentials | تأهيل القوى العاملة العمانية لعصر الذكاء الاصطناعي: أساسيات إدارة التغيير | Repair | 2026-10-07 | [2026-10-07-upskilling-your-omani-workforce-for-the-ai-era-change-manage](https://aiprofitlab.io/blog/en/2026-10-07-upskilling-your-omani-workforce-for-the-ai-era-change-manage/) |
| 49 | Cluster 5: Executive Strategy, Vision 2040 & ROI | The CEO Guide to Customized Dashboard Analytics and Automated Business Reporting | دليل المدير التنفيذي للوحات التحكم المخصصة وتقارير الأعمال المؤتمتة | Repair | 2026-10-08 | [2026-10-08-the-ceo-guide-to-customized-dashboard-analytics-and-automate](https://aiprofitlab.io/blog/en/2026-10-08-the-ceo-guide-to-customized-dashboard-analytics-and-automate/) |
| 50 | Cluster 5: Executive Strategy, Vision 2040 & ROI | Future-Proofing Omani Businesses: Key AI Trends to Watch in the GCC for 2026–2030 | تأمين مستقبل الشركات العمانية: أبرز اتجاهات الذكاء الاصطناعي في الخليج 2026-2030 | Repair | 2026-10-09 | [2026-10-09-future-proofing-omani-businesses-key-ai-trends-to-watch-in-t](https://aiprofitlab.io/blog/en/2026-10-09-future-proofing-omani-businesses-key-ai-trends-to-watch-in-t/) |
| 58 | Cluster 6: Technical Implementation & Integrations | How Vector Databases (Pinecone, Qdrant) Power Semantic Search for GCC Websites | كيف تمكّن القواعد البيانية المتجهة البحث الدلالي للمواقع في الخليج | Repair | 2026-10-10 | [2026-10-10-how-vector-databases-pinecone-qdrant-power-semantic-search-f](https://aiprofitlab.io/blog/en/2026-10-10-how-vector-databases-pinecone-qdrant-power-semantic-search-f/) |

---

## Daily Routine SOP

Automated by `.github/workflows/daily_publish.yml` (03:17 UTC = 07:17 Muscat), which runs
`execution/daily_publish.py`. The rules are the article-creator skill
(`Website/SKILL_article_creator/SKILL.md`); the script sends its Step 1 criteria to the model verbatim.

1. Take the first `Pending` row. A row whose English title is more than 65% similar to a published
   article is marked `Skipped` (skill Step 0). When fewer than 2 rows are `Pending`, the model proposes
   6 new topics and appends them here. Edit or delete them freely; rows run top to bottom.
2. Gemini writes the EN article, then the AR edition, as structured JSON. Each is audited against the
   skill: 800–1200 body words (AR 650–1350), exactly 10 FAQs, at least 3 question H2s, a table, at
   least 3 Oman/GCC references, meta description 140–155 characters, no banned phrases, internal links.
   A failing draft goes back with its failures listed, up to 3 attempts. Every reference URL is fetched;
   dead ones are unlinked and dropped.
3. A hero image is generated for this article (light-mode brand style), checked, and saved under a
   new hashed filename (`/blog/images/` is cached as immutable for a year).
4. The source is rendered in the skill's marker contract, then derivatives → `reskin_articles.py --only`
   → `reskin_blog_hubs.py` → `run_sitemap.py` → `build_aiden_index.py`, every exit code enforced.
5. Status becomes `Published` with the date and link. The forum snippet (skill Step 8) is appended
   to `directives/forum_snippets.md`.
6. The workflow commits, deploys (everything since the server's last good deploy, recorded in
   `/.deployed-commit`), then checks the live EN + AR pages and hero.

Any failure stops the run before anything is committed. GitHub emails the failure, and the topic stays
`Pending` for the next day.

**By hand**
- `python3 execution/daily_publish.py --dry-run`: writes the draft to `.tmp/daily_publish/<slug>/`,
  publishes nothing. Then `--from-dir <that folder>` publishes it without calling the API again.
- `--repair <slug>`: regenerates an existing article at the same URL and date (or use the Run workflow
  button with the `repair` input).
- `--preflight`: checks the API key, the models and Pillow. Needs `GEMINI_API_KEY` in `.env` locally,
  or as a repository secret in GitHub.
- Models: `GEMINI_TEXT_MODELS` / `GEMINI_IMAGE_MODELS` (comma-separated, tried in order).

**Learned 2026-10-13** (why the first version failed): it published a placeholder page whenever the
API call failed; it copied one stock `default.png` onto every article; CI never installed Pillow, so
derivatives silently failed; it deployed before committing, so each article reached the server a day
late or never (the deploy uploaded only `HEAD~1..HEAD`); and it marked every topic Published regardless.
Gemini 2.5 Flash Image was shut down on 2026-10-02; use the 3.1 image models.
