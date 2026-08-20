A B U I L D J O U R N A L — V 2 

# G O L E S TA N 

T E A 



از ایده تا وبسایت الکچری 

— تولید با **CINEMATIC SCROLL** یک راهنمای گامبهگام برای ساخت وبسایت برند الکچری چای گلستان با الگوی . Vercel  وClaude Code، GitHub ، و توسعه باKling ، انیمیشن باChatGPT 

C R A F T E D B Y 

N A B U 

C O N T E N T S · ت س ر ه ف 0 2 

I N D E X 

## Contents 



|ه در این راهنما خواهید یافت<br>01<br>O V E R V I E W|آنچ<br>03<br>مرور پروژه|
|---|---|
|02<br>S C E N E I M A G E P R O M P T S|05<br>پرامپتهای تصویر|
|03<br>M O T I O N P R O M P T S ( K L I N G<br>3 . 0 )|09<br>پرامپتهای انیمیشن|
|04<br>V I D E O A S S E M B L Y|12<br>ساخت ویدیو نهایی|
|05<br>B U I L D W I T H C L A U D E C O D E|13<br>توسعه با کلود کد|
|06<br>B I L I N G U A L L AY E R ( E N · FA )|16<br>لیه دوزبانه|
|07<br>G I T H U B & V E R C E L D E P L O Y|17<br>انتشار نهایی|
|08<br>M A K E I T Y O U R S|18<br>شخصیسازی|
|09<br>T H E D O U B L E - E D G E D S W O R D<br>G O L E S T A N B U I L D G U I D E|19<br>شمشیر دولبه<br>0 2|



G O L E S T A N B U I L D G U I D E 

~ 3 0 M I N · R E A D 

C H A P T E R 0 1 

### Overview 

##### مرور پروژه 

در این پروژه میخواهیم یک وبسایت الکچری برای برند چای ایرانی «گلستان» بسازیم. قلب طراحی، الگویی است که آن را مینامیم — ویدیوی هیرو با اسکرول کاربر پیش میرود، صحنه به صحنه: از سقوط چایکیسه در فضای **Cinematic Scroll** تاریک، تا انفجار مواد، ریختن در لیوان، دم کشیدن، و در نهایت دستان یک زن ایرانی که لیوان را در آغوش میگیرد. 

S T A C K — ی ژ و ل و ن ک ت 

###### ابزارهای مورد استفاده 

• Nano Banana (Google)  یاChatGPT (gpt-image-1) :تولید تصاویر صحنهها • Kling 3.0 (image-to-video) :انیمیشن صحنهها Premiere  یاCapCut :مونتاژ ویدیو • • Claude Code + Next.js 14 (App Router) + TypeScript :توسعهی وب • Tailwind CSS ،( )انیمیشن میکروFramer Motion ،( )اسکرولGSAP + ScrollTrigger :کتابخانهها GitHub :مدیریت کد • Vercel :انتشار • 

F L O W — ر ا ن ک ا ی ر ج 

###### مراحل کلی پروژه 

ChatGPT  تصویر کلیدی برای صحنههای ویدیو با پرامپتهای **۶** . ساخت۱ • Kling 3.0  ثانیهای با۵–۳ . تبدیل هر تصویر به ویدیوی کوتاه۲ • . اتصال کلیپها به یک ویدیوی واحد و خروجی با تنظیمات مناسب وب۳ • و اضافه کردن اسکرول هیروClaude Code  باNext.js . ساخت پروژه۴ • • Vercel  و دیپلوی رویGitHub . آپلود روی۵ 

C H A P T E R 0 1 — O V E R V I E W 

0 3 

E S T · 2 0 2 6 · N A B U 

D E S I G N S Y S T E M — ی ح ا ر ط 

پالت رنگ و فونت 



پسزمینه 

```
#000000
```

قرمز تیره 

```
#8B0000
```

طالیی عتیقه 

```
#C9A961
```

کرم روشن 

```
#F5F1E8
```

F O N T — T I T L E 

#### Cormorant Garamond 

F O N T — B O D Y 

###### Inter — clean, modern, neutral. 

F O N T — F A R S I 

وزیرمتن — برای متن فارسی 

N O T E → ه ت ک ن 

اسم «گلستان» در فارسی یعنی باغ گل. به همین دلیل گلبرگهای سرخ در تمام صحنهها بهعنوان امضای بصری برند 

تکرار میشوند. 

C H A P T E R 0 1 — O V E R V I E W 

0 4 

~ 1 H R · $ 5 O P E N A I 

###### C H A P T E R 0 2 

### Scene Prompts 

##### پرامپتهای تصویر صحنهها 

تصویر کلیدی ویدیو آورده شده است. این تصاویر بهعنوان فریم شروع و پایان **۶** در این فصل، پرامپتهای نهایی برای ساخت هر کلیپ ویدیویی استفاده میشوند. 

###### G L O B A L S T Y L E → ی م و م ل ع ی ا ت س ا 

.این عبارت را به ابتدای تمام پرامپتها اضافه کنید تا یکدستی بصری حفظ شود 

_cinematic product photography, deep black background with dark crimson red gradient, warm gold rim lighting from above, ultra detailed, 8k, shallow depth of field, luxury editorial, moody,_ **_16:9 aspect ratio_** _(desktop hero)._ 

01 

T H E D E S C E N T 

.صحنهی سقوط: چایکیسه به آرامی در فضای تاریک پایین میآید 

###### P R O M P T 

_a single unbleached muslin teabag with twine string and small kraft paper tag descending slowly through pure void from above, captured mid-fall, the twine string trailing upward into darkness, dramatic golden spotlight from top catching the fabric texture and creating a long soft shadow, fine dust particles and tea fragments suspended in the light beam around the bag, deep crimson atmospheric haze bleeding into pure black at the edges, cinematic depth, the bag is the only subject, hero product shot._ 

C H A P T E R 0 2 — S C E N E P R O M P T S 

0 5 

S C E N E 0 2 · 0 3 

02 

T I T L E R E V E A L 

.پردهبرداری از نام برند: کیسه باز میشود و جوانهای سبز از داخل آن سر بیرون میآورد 

###### P R O M P T 

_the same unbleached muslin teabag centered in frame, slowly splitting open along the top seam, a single fresh green tea leaf sprout emerging upward from inside as if growing, dark whole tea leaves and a few rose petals spilling from the opening and cascading down the sides of the bag, twine string taut from above, dramatic golden god-ray spotlight from top illuminating the sprout, elegant thin serif wordmark "GOLESTAN TEA" in muted antique gold floating in the background behind the bag with subtle letter-spacing, deep crimson atmospheric haze, dust particles suspended in the light beam, cinematic hero composition._ 

03 

###### T H E B U R S T 

.انفجار: کیسه از هم میپاشد و شش ماده اصلی بهصورت متقارن در هوا منفجر میشوند 

###### P R O M P T 

_the unbleached muslin teabag fully splits open in mid-air at the center of the frame, six ingredients explosively outward in a perfectly symmetrical radial burst — fresh green tea leaves, deep crimson dried rose petals leading the explosion, whole green cardamom pods, cinnamon bark shards, clove buds, and black peppercorns — frozen at the peak of the explosion, golden dust and tea particles suspended in the air between them, dramatic god-ray spotlight from above catching every petal and leaf edge, the rose petals are the visual hero of the burst, twine string trailing upward, deep crimson void background fading to pure black at the corners, hyper-detailed slow- motion product cinematography._ 

C H A P T E R 0 2 — S C E N E P R O M P T S 

0 6 

S C E N E 0 4 · 0 5 

04 

T H E F A L L 

.سقوط مواد: مواد منفجرشده به داخل لیوان شیشهای پر از آب گرم میریزند 

###### P R O M P T 

_clear glass mug with handle filled with hot golden amber water sitting in the center of the frame, the six exploded ingredients cascading down into it from above — deep crimson rose petals leading the fall, followed by fresh green tea leaves, whole green cardamom pods, cinnamon bark shards, clove buds, and black peppercorns — captured at the exact moment the first petals hit the water surface, a delicate crown-shaped splash rising upward, fine water droplets suspended mid-air, the rest of the ingredients still falling through the air above the mug, first wisps of steam beginning to curl up, dramatic golden spotlight from above catching every droplet and petal, deep crimson void background fading to pure black at the edges, hyper slow-motion luxury product cinematography._ 

05 

###### T H E S T E E P 

.دم کشیدن: مواد در آب میچرخند و رنگ آب بهتدریج عسلی میشود 

###### P R O M P T 

_clear glass mug with handle viewed straight on at eye level, filled with golden amber tea actively brewing, deep crimson rose petals, fresh green tea leaves, whole green cardamom pods, cinnamon bark shards, clove buds, and black peppercorns suspended and gently swirling throughout the water, the liquid well in motion from the steam impact with visible swirls and currents, color slowly deepening from pale gold to rich amber as the tea steeps, soft steam beginning to curl upward from the surface, warm light glowing through the glass from behind and above, dramatic golden spotlight illuminating the mug, deep crimson void background fading to pure black at the edges, intimate macro detail, hyper-detailed product cinematography._ 

C H A P T E R 0 2 — S C E N E P R O M P T S 

0 7 

S C E N E 0 6 

06 

###### T H E R I T U A L 

.آیین: دستان یک زن ایرانی با پوست گرم زیتونی، لیوان را با احترام در آغوش میگیرند 

###### P R O M P T 

_two graceful hands of an Iranian woman cradling a clear glass mug with handle filled with fully steeped golden amber tea, warm olive-toned skin, delicate slender fingers gently curled around the glass body of the mug with reverence, soft natural manicured nails, a hint of an elegant gold ring or thin bracelet visible, the deep crimson rose petals, green tea leaves, and whole spices visible inside the mug, thick ribbons of steam rising upward and curling into the light, hands and mug lit warmly by the golden glow of the tea itself, dramatic golden spotlight from above catching the steam, deep crimson void background fading to pure black at the edges, intimate cinematic framing, hyper-detailed luxury product photography, the moment of offering._ 

###### T I P → ه ت ک ن 

،برای حفظ یکدستی، نگهداشتن لیوان شیشهای با دسته در همهی صحنهها مهم است. هر بار که پرامپت مینویسید » را تکرار کنید. clear glass mug with handle« دقیقاً کلمات 

###### B G R E M O V A L → ه ن ی م ز س ف پ ذ ح 

بهسادگیrembg  یاImageMagick اگر تصاویر محصول )یا لوگو( با پسزمینهی سفید/قرمز تولید شدند، با پسزمینه را حذف کنید: 

```
convert input.jpg -fuzz 8% -fill none -floodfill +0+0 white -trim out.png
```

C H A P T E R 0 2 — S C E N E P R O M P T S 

0 8 

~ 2 H R · ~ $ 3 0 K L I N G 

###### C H A P T E R 0 3 

### Motion Prompts 

##### Kling 3.0 پرامپتهای انیمیشن برای 

. ثانیه( بسازد۵  تا۳)  میدهیم تا یک کلیپ کوتاهKling 3.0  تصویر کلیدی آماده است، هر جفت تصویر متوالی را به۶ ح ل که استفاده کنید. Start + End Frame  از حالتKling در 

01 

S C E N E 1 · D E S C E N T 

.انیمیشن سقوط آرام چایکیسه از ب ل به مرکز فریم 

###### M O T I O N P R O M P T 

_slow cinematic descent, the teabag falls gracefully from the top of the frame to the center, twine string trailing naturally above it, gentle subtle sway as it descends, dust particles drifting slowly in the golden light beam, camera locked static, slow motion 24fps feel, smooth easeout as the bag settles into final position, luxury product film, no camera movement, focus stays sharp on the bag throughout._ 

0 9 

C H A P T E R 0 3 — M O T I O N P R O M P T S 

M O T I O N 2 · 3 

S C E N E 2 → 3 · B U R S T 

02 

.کیسه باز میشود و مواد بهصورت شعاعی منفجر میشوند 

###### M O T I O N P R O M P T 

_the teabag tears open dramatically along the top seam, the wordmark "GOLESTAN TEA" gently fades into the crimson haze as the action takes over, ingredients burst outward from inside the bag in a slow-motion radial explosion, rose petals lead the burst followed by green tea leaves and whole spices spiraling outward, the bag fabric ripples from the force of the release, twine string whips slightly upward, golden dust and particles scatter through the light beam,_ 

_camera locked static with no zoom or pan, slow-motion 24fps cinematic feel, smooth ease-out as the explosion reaches its peak, luxury product film, sharp focus throughout._ 

03 

###### S C E N E 3 → 4 · T H E F A L L 

.انفجار آرام میشود و مواد به داخل لیوانی که از پایین فریم وارد میشود میریزند 

###### M O T I O N P R O M P T 

_the frozen explosion releases and gravity takes over, the muslin teabag dissolves and fades away into the crimson haze, all six ingredients begin falling downward in a graceful slow-motion cascade, rose petals lead the descent followed by green tea leaves and whole spices spreading gently as they fall, a clear glass mug with handle filled with golden amber water rises into view from the bottom of the frame to receive them, the first rose petals hit the water surface creating a delicate crown-shaped splash, water droplets suspend mid- air at the impact moment, first wisps of steam begin to curl upward, camera locked static with no pan or zoom, slow-motion 24fps cinematic feel, smooth ease-in as the fall and ease-out on the splash, luxury product film, sharp focus throughout._ 

C H A P T E R 0 3 — M O T I O N P R O M P T S 

1 0 

M O T I O N 4 · 5 

04 

S C E N E 4 → 5 · T H E S T E E P 

.آب آرام میشود، مواد در لیوان میچرخند و رنگ چای عمیقتر میشود 

###### M O T I O N P R O M P T 

_the crown splash collapses gently back into the surface of the tea, the remaining falling ingredients complete their descent into the mug one by one creating small ripples, water droplets suspended in air fall back down, all six ingredients begin swirling slowly inside the mug creating gentle currents and visible water motion, the liquid color slowly deepens from pale gold to rich amber as the tea steeps, rose petals drift in slow circles through the water, steam begins to rise more steadily from the surface curling upward into the light, camera locked static with no pan or zoom, slow-motion 24fps cinematic feel, smooth ease-out as the swirling settles into a gentle rhythm, luxury product film, sharp focus throughout._ 

05 

###### S C E N E 5 → 6 · H A N D S C R A D L E 

.دستان زن ایرانی از دو طرف وارد فریم میشوند و لیوان را در آغوش میگیرند 

###### M O T I O N P R O M P T 

_the swirling tea inside the mug gently settles, the liquid color fully deepens to rich amber, two graceful hands of an Iranian woman with warm olive-toned skin slowly emerge from both sides of the frame and move gently inward toward the mug, delicate slender fingers softly wrap around the glass body of the mug from both sides with reverence, a subtle hint of gold jewelry catches the light as the hands settle into place, steam continues to rise and curl upward into the golden light beam, the warm glow of the tea illuminates the hands from within, camera locked static with no pan or zoom, slow-motion 24fps cinematic feel, smooth ease-out as the hands approach and ease-out as they settle around the mug, luxury product film, sharp focus throughout._ 

C H A P T E R 0 3 — M O T I O N P R O M P T S 

1 1 

~ 4 5 M I N · F R E E 

###### C H A P T E R 0 4 

### Video Assembly 

##### ساخت ویدیو نهایی 

. داریم. این کلیپها باید پشت سر هم چیده شوند و بهصورت یک ویدیوی پیوسته خروجی گرفته شوندKling  کلیپ از۵ ح ل انتخاب ساده و رایگانی است. CapCut S T E P 0 1 وارد کردن کلیپها کنید. هر کلیپ را پشت سر کلیپ قبلی قرار دهید بدون فاصله یاCapCut Import  را به ترتیب درKling  کلیپ۵ تمام . overlap 

S T E P 0 2 

ترنزیشن نرم بین کلیپها 

. ثانیه قرار دهید تا انتقالها روان و سینمایی باشند۰.۳  با مدتCross Dissolve بین هر دو کلیپ یک 

S T E P 0 3 

تنظیمات خروجی 30fps :فریمریت • (16:9 ، )هیرو دسکتاپ **1080×1920** :رزولوشن • • H.264 (MP4) :کدک Mbps 12–8 :بیتریت • • (Mute) صدا: حذف کنید • ( ثانیه )برای اسکرول روانKeyframe Interval: ۱ 

P R O T I P → ی ا ه ف ر ه ح ت ک ن 

seek  آن را ترجیح میدهند و در اسکرول سریعترFirefox  وChrome . هم خروجی بگیریدWebM (VP9) یک نسخه استفاده میکند. MP4 fallback  ازSafari .میکنند 

C H A P T E R 0 4 — V I D E O A S S E M B L Y 

1 2 

~ 2 H R · $ 0 

###### C H A P T E R 0 5 

### Build with Claude Code 

##### Claude Code توسعه وبسایت با 

راclaude  بسازیم. ترمینال را باز کنید و دستورClaude Code  را باNext.js ح ل که ویدیوی نهایی آماده است، میتوانیم پروژه اجرا کنید. 

S T E P 0 1 

###### آمادهسازی فولدر پروژه 

( را داخل آن قرار دهید، سپس ترمینال را در همان فولدر بازlogo.svg) ( و لوگوhero.mp4) یک فولدر جدید بسازید، فایل ویدیو 

کنید. 

```
mkdir golestan-tea && cd golestan-tea
mkdir public
# put hero.mp4 and logo.svg inside /public
claude
```

F O L D E R T R E E 

ساختار نهایی فولدر 

|`golestan-tea/`|
|---|
|`├── app/`|
|`│   ├── layout.tsx`<br>|
|`│   ├── page.tsx`<br>|
|`│   └── globals.css`|
|`├── components/`|
|`│   ├── HeroVideo.tsx`<br>|
|`│   ├── Navbar.tsx`<br>|
|`│   ├── Products.tsx`<br>|
|`│   ├── ProductCard.tsx`<br>|
|`│   ├── Footer.tsx`<br>|
|`│   ├── CustomCursor.tsx`<br>|
|`│   └── LangToggle.tsx`<br>|
|`├── lib/`<br>|
|`│   ├── gsap.ts`<br>`│   └── lang.tsx`<br>`├── public/`|



```
│   ├── hero.mp4
│   ├── hero-poster.jpg
│   ├── golestan.png
│   └── products/
│       ├── earl-grey.png
│       ├── ceylon-gold.png
│       └── premium-indian.png
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

C H A P T E R 0 5 — B U I L D 

1 3 

M A S T E R P R O M P T 

S T E P 0 2 

###### Claude Code پرامپت اصلی برای 

. کنید — تمام جزئیات طراحی، ساختار صفحه، و تعامالت در آن آمده استClaude Code paste پرامپت زیر را در 

###### ▢ R O L E 

```
Build a luxury single-page website for "GOLESTAN TEA" — a premium Persian-inspired tea brand.
```

###### ▢ T E C H S T A C K 

```
Next.js 14 (App Router) · TypeScript · Tailwind CSS · GSAP + ScrollTrigger (scroll-synced video) ·
Framer Motion (micro-interactions).
```

###### ▢ A S S E T S 

```
/public/hero.mp4 (1920×1080 H.264) · /public/hero-poster.jpg (first frame) · /public/golestan.png
(logo, transparent) · /public/products/*.png (3 product shots, transparent).
```

###### ▢ D E S I G N S Y S T E M 

```
bg pure black #000000 · accent dark crimson #8B0000 → #4A0000 · highlight antique gold #C9A961 ·
text off-white #F5F1E8 · headlines Cormorant Garamond (300/400) · body Inter (300/400) · smallcaps
utility: uppercase + 0.35em tracking.
```

###### ▢ S T R U C T U R E 

```
Fixed Navbar (mix-blend-difference text, transparent → blur on scroll) · HERO scroll-synced video
(400–500vh tall, sticky video element, GSAP scrub maps scroll progress → video.currentTime,
overlay headlines fade in/out at 15–25, 35–45, 60–70, 85–100% scroll) · PRODUCTS section "THE
COLLECTION" (3 cards: Earl Grey · Ceylon Gold · Premium Indian, hover: scale 1.02, gold border
glow, floating ingredient chip with frosted glass) · Footer (logo, gold divider, © mark, IG/X
icons).
```

###### ▢ P O L I S H 

```
custom gold-dot cursor with lerp · film grain overlay (~4% opacity) · vignette on hero · inset
gallery frame with corner brackets · ALL transitions ease-out 0.6s–1.2s.
```

###### ▢ P E R F O R M A N C E 

```
lazy-load Products · video poster prevents layout shift · use next/image for product photos · iOS
Safari: playsInline + muted + preload="auto" + explicit video.load(), seek only when paused.
```

C H A P T E R 0 5 — B U I L D 

1 4 

D E V · D E B U G 

S T E P 0 3 

###### تست محلی 

. را باز کنیدlocalhost:3000 ، با دستور زیر سرور محلی را اجرا کنید و در مرورگرClaude Code پس از اتمام ساخت توسط 

```
npm run dev
```

S T E P 0 4 

###### iteration اصالحات و 

:ً بگویید کجا باید تنظیم شود. مثالClaude Code اگر اسکرول روان نیست یا متنها در زمان نامناسبی ظاهر میشوند، به 

_The text "GOLESTAN TEA" appears too early. Shift it to 20-30% scroll range and make the fade-in smoother with 1.5s ease-in-out. Also reduce the video section height from 400vh to 500vh so the scrub feels less hurried._ 

S T E P 0 5 

###### بهینهسازی ویدیو 

بارگذاریmedia query  پایینتر( برای موبایل بسازید و باbitrate  با720p ًاگر ویدیو سنگین است، یک نسخه فشرده )مثال بسازید: ffmpeg keyframe-per-frame کنید. برای اسکرول روان، با 

```
ffmpeg -i hero.mp4 -an -c:v libx264 -crf 22 \
```

```
  -x264-params "keyint=1:min-keyint=1:scenecut=0" \
```

```
  -movflags +faststart hero-scrub.mp4
```

D E B U G → گ ا ع ب ف ر 

"preload="auto  وmuted، playsinline هایattribute  اجرا نمیشود، مطمئن شوید کهSafari iOS اگر ویدیو در صدا بزنید. seek )( را قبل ازvideo.load  تنظیم شدهاند. همچنینvideo روی تگ 

C H A P T E R 0 5 — B U I L D 

1 5 

~ 3 0 M I N · B I L I N G U A L 

###### C H A P T E R 0 6 

### Bilingual Layer 

##### )الیه دوزبانه (انگلیسی · فارسی 

باعث میشود وبسایت برای هر دو مخاطب بومی و بینالمللی کار کند. الیهtoggle EN / FA برای برند ایرانی، اضافه کردن یک طراحی ثابت میماند )لوکیشن، فریم، اسکرول(، فقط محتوای متنی عوض میشود. 

###### F O N T — ت ن و ف 

###### فونت فارسی 

را حفظ میکند ولی برای گلیفهایCormorant  اضافه کنید. این فونت ظرافتlayout.tsx  را بهGoogle Fonts  ازVazirmatn .فارسی بهینه است 

```
import { Vazirmatn } from 'next/font/google';
const farsi = Vazirmatn({
  subsets: ['arabic', 'latin'],
  variable: '&-font-fa',
});
```

C O N T E X T — ت س ک ت ن ا ک 

###### سیستم ترجمه 

)( ارائه دهد. تمام رشتههاuseLang  به نامhook ( که زبان فعلی را نگه دارد و یکlib/lang.tsx)  بسازیدReact Context یک پایدار میماند. localStorage > ذخیره میشوند. زبان انتخابی درRecord>Lang, Strings  از نوعtable در یک 

T O G G L E — ه م ک د 

###### Navbar  درEN / FA دکمه 

)( راsetLang →  کنار هم با جداکننده طالیی است. زبان فعال طالیی، غیرفعال کمرنگ. کلیک میکندbutton دکمه شامل دو کل سایت فوراً عوض میشود. →صدا میزند 

T I P → ه ت ک ن 

استفاده کنید )نهkey={i}  ازmap  هنگام عوض شدن زبان، درScrollTrigger  شدنremount برای جلوگیری از C H A P T E R 0 6 — B I L I N G U A L بروز شود. textContent ها ثابت بمانند و فقطDOM element ( تاkey={headline} 1 6 

~ 1 5 M I N · F R E E 

###### C H A P T E R 0 7 

### Deploy 

##### Vercel  وGitHub انتشار با 

میگیرد و سایت راbuild  بهصورت خودکارVercel . متصل کنیدVercel  کنید و سپس بهGitHub push آخرین قدم: کد را به روی دامین رایگان منتشر میکند. 

###### S T E P 0 1 

###### GitHub ساخت ریپو در 

هر کدام مناسبPublic  یاPrivate  بسازید. بهصورتgolestan-tea  شوید و یک ریپازیتوری جدید با نامgithub.com وارد 

بود. 

S T E P 0 2 

###### کردن کدPush 

.دستورات زیر را در ترمینال فولدر پروژه اجرا کنید 

```
git init
git add .
```

```
git commit -m "initial commit — golestan tea launch"
git branch -M main
```

```
git remote add origin https:&/github.com/USERNAME/golestan-tea.git
git push -u origin main
```

###### S T E P 0 3 

###### Vercel اتصال به 

را انتخابgolestan-tea  کلیک کنید، ریپوImport Project  خود الگین کنید. رویGitHub  شوید و با حسابvercel.com وارد را بزنید. Deploy  را تأیید کنید وNext.js کنید. تنظیمات پیشفرض 

C R I T I C A L → م ه ر م ا د ش ه 

& Settings → Build ،(. اگر اشتباه شدOther  تنظیم کنید )نه **Next.js** را رویFramework Preset ًحتما کنید. redeploy  را عوض کنید وDevelopment → Framework 

C H A P T E R 0 7 — D E P L O Y 

1 7 

C U S T O M D O M A I N 

S T E P 0 4 

###### )دامین سفارشی (اختیاری 

Vercel  را بهDNS ( را اضافه کنید وgolestan.tea ً، دامین اختصاصی خود )مثالSettings → Domains ، بخشVercel در متصل کنید. D O N E → د م ش ا م ت بهصورت خودکارVercel ، کنیدGitHub push  ح ل روی اینترنت است. هر بار که کد را بهGolestan Tea سایت میکند. deploy نسخه جدید را 

C H A P T E R 0 8 

### Make It Yours 

##### شخصیسازی 

این راهنما برای چای گلستان نوشته شده، اما ستون فقرات آن برای هر برند الکچری دیگری کار میکند. برای شخصیسازی، این 

پنج چیز را عوض کنید: 

• را با لوگوی برند خود جایگزین کنید.public/golestan.png/ — **لوگو** • را تغییر دهید.crimson  وgold  متغیرهایtailwind.config.ts  — در **پالت رنگ** • (.Playfair، EB Garamond، Italiana)  الکچری دیگری عوض کنیدserif  را با هرCormorant Garamond — **فونت** • را با نام، قیمت و تصاویر محصوالت خود بهروز کنید.components/Products.tsx — **محصوالت** صحنه را با ریتم برند خود بازنویسی کنید )مثالً برای عطر، کفش، جواهر(.۶  — این **ویدیوی هیرو** • 

C H A P T E R 0 8 — M A K E I T Y O U R S 

1 8 

C A U T I O N · E X E C U T I O N M A T T E R S 

C H A P T E R 0 9 

### The Double-Edged Sword علیه شما کار میکندCinematic Scroll شمشیر دولبه — وقتی 

ل میبردbounce rate)  اگر درست اجرا شود، نرخ پرش( را کاهش میدهد، زمان حضور در سایت را ب **Cinematic Scroll** الگوی میگیرید — کاربر سریعتر ترک **معکوس** و فروش را افزایش میدهد. اما اگر در یکی از حوزههای زیر کوتاهی شود، دقیقاً نتیجهی میکند، اعتمادش از بین میرود، و برداشت برند صدمه میبیند. R I S K 0 1 — ل و ر ک س ی ا د ن گ و ک ل 

###### پرفورمنس ضعیف 

• . کنیدkeyframe-per-frame encode ً دارد — حتماstutter  با هر اسکرول حالتvideo.currentTime اگر • . ایدهآل استCRF 23–26 . نگهدارید **مگابایت۲۵** سایز ویدیو زیر • . فقط برای دسکتاپ سرو کنیدmedia query  ثانیه است، ویدیو را با۴  ب لیLCP  مدل موبایل را اجرا کنید. اگرLighthouse 

R I S K 0 2 — ب ا ر ل خ ی ا ب و م 

###### Android  وiOS رندر ضعیف روی 

. نمیکندstart ً ویدیو را اصال **"muted + playsInline + preload="auto** بدونiOS Safari • . کاهش دهید یا یک پوستر استاتیک نمایش دهید250vh  بخش هیرو را بهheight ، یا768px روی صفحههای کوچکتر از • • . را غیرفعال کنید و صرفاً پوستر را نشان دهیدscrub ، داردprefers-reduced-motion اگر کاربر 

R I S K 0 3 — ر ی و ا ص و و ت ی د ی ف و ی ع ت ض ی ف ی ک 

###### پایین آمدن استانداردهای بصری 

• وobject-contain  به نظر برسند، حس "الکچری" فوراً از بین میرود — باupscaled  یاpixelated اگر تصاویر محصول .stretch  سخاوتمندانه نمایش دهید، نهpadding .ویدیویی با اکسپوژر اشتباه یا فریمهای نامتعادل بدتر از نداشتن ویدیو است • • .(floodfill  یاrembg) پسزمینه سفید روی کارتهای محصول دارک = کالش بصری. حتماً حذف کنید 

R I S K 0 4 — ف ی ع ت ض ی ا و ن و ر ت م 

لور بیجذابیت 

• . متنی باید یک تصمیم کوچک بگیرد: اطالعات بدهد، احساس بسازد، یا کنجکاوی ایجاد کندoverlay هر • .متن کلیشهای )"کیفیت برتر"، "بهترین چای"( = کاربر از کار میافتد. ریتم باید مثل شعر باشد، نه بروشور 

. متمرکز نشوید — خواننده صبور نیستoverlay  روی یک **ثانیه۵  تا۴** هیچوقت بیش از • 

B O T T O M L I N E → ی ی ا ه ی ن ه ج ی ت ن 

— قوی باشند، کاربر مسحور **پرفورمنس، کیفیت بصری، لور** —  قمار است. اگر هر سه ضلعCinematic Scroll میشود و وبسایت شما بهعنوان "تجربه" در ذهن میماند، نه فقط یک فروشگاه. اگر یکی از این سه ضعیف باشد، **پس قبل از انتشار، روی موبایل واقعی تست کنید، نه فقط روی** ثانیه میرود و دیگر برنمیگردد. ۲ کاربر در عرض **.DevTools** 

C H A P T E R 0 9 — T H E D O U B L E - E D G E D S W O R D 

1 9 

_"Pour. Wait. Breathe."_ 

.بریز. صبر کن. نفس بکش 



G O L E S T A N — C R A F T E D B Y N A B U 

V 2 · M M X X V I 

