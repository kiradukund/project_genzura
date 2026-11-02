# Kinyarwanda translation review

The feature spec requires a second native Kinyarwanda speaker to review every translation before launch.
Tick each line when it is approved, or write the correction in the last column.

**Source:** *handoff* = Alier's working translation from the handoff document. *new draft* = written afterwards and needs the closest review.

The three example scam messages (`samples.text.*`) stay in English on purpose: the backend rules only recognise English, so translated examples would score LOW RISK.

Put approved changes in `frontend/src/i18n/rw.json` (website) and `backend/app/messages.py` (USSD/SMS). After changing `messages.py`, run `pytest` in `backend/`. It checks that USSD/SMS text uses only characters basic phones can show and fits the length limits.

## Website (`frontend/src/i18n/rw.json`)

| OK | Key | English | Kinyarwanda | Source | Correction |
|---|---|---|---|---|---|
| [ ] | `title` | Check before you pay | Suzuma mbere yo kwishyura | handoff | |
| [ ] | `subtitle` | Verify overseas job offers, scholarships and visas to avoid scams | Genzura amatangazo y'akazi, buruse na viza byo hanze y'igihugu wirinde uburiganya | handoff | |
| [ ] | `language` | Language | Ururimi | new draft | |
| [ ] | `nav.label` | Main menu | Ibikubiyemo | new draft | |
| [ ] | `nav.menu` | Open menu | Fungura ibikubiyemo | new draft | |
| [ ] | `nav.how` | How it works | Uko bikora | new draft | |
| [ ] | `nav.check` | Check an offer | Suzuma itangazo | new draft | |
| [ ] | `nav.signs` | Warning signs | Ibimenyetso | new draft | |
| [ ] | `nav.report` | Report a scam | Tanga raporo | new draft | |
| [ ] | `home.cta` | Check an offer now | Suzuma itangazo nonaha | new draft | |
| [ ] | `home.trust` | Free · Private · Results in seconds | Ni ubuntu · Ibanga ryawe rirarinzwe · Igisubizo mu masegonda | new draft | |
| [ ] | `home.stepsTitle` | How it works | Uko bikora | new draft | |
| [ ] | `home.steps.1.title` | Paste or upload the offer | Shyiramo itangazo | new draft | |
| [ ] | `home.steps.1.body` | Copy the WhatsApp message or email, or upload a screenshot. Choose job, scholarship or visa. | Koporora ubutumwa bwa WhatsApp cyangwa imeli, cyangwa ushyireho ifoto yabwo. Hitamo akazi, buruse cyangwa viza. | new draft | |
| [ ] | `home.steps.2.title` | Get a risk level in seconds | Menya urugero rw'ibyago mu masegonda | new draft | |
| [ ] | `home.steps.2.body` | Genzura checks the offer for known scam signs and shows exactly which red flags it found. | Genzura isuzuma itangazo ishakisha ibimenyetso by'uburiganya bizwi, ikakwereka neza ibyo yabonye. | new draft | |
| [ ] | `home.steps.3.title` | Act safely | Irinde | new draft | |
| [ ] | `home.steps.3.body` | Never pay before you verify. Report scams to RIB on 166 or get help from a Digital Ambassador. | Ntukishyure utabanje kugenzura. Tanga raporo kuri RIB kuri 166 cyangwa usabe ubufasha Umuhuzabikorwa w'Ikoranabuhanga. | new draft | |
| [ ] | `home.checkTitle` | Check an offer | Suzuma itangazo | new draft | |
| [ ] | `home.signsTitle` | What Genzura looks for | Ibyo Genzura ireba | new draft | |
| [ ] | `home.signsIntro` | Common signs of fake overseas offers. The more signs an offer has, the higher its risk. | Ibimenyetso bikunze kugaragara mu matangazo y'ibinyoma yo hanze. Uko itangazo rifite ibimenyetso byinshi, ni ko ibyago byiyongera. | new draft | |
| [ ] | `home.ribTitle` | Already paid, or being pushed to pay? | Waba waramaze kwishyura, cyangwa uri guhatirwa kwishyura? | new draft | |
| [ ] | `home.ribBody` | Stop sending money and report it to the Rwanda Investigation Bureau. | Hagarika kohereza amafaranga, maze utange raporo ku Rwego rw'Igihugu rw'Ubugenzacyaha (RIB). | new draft | |
| [ ] | `offerType.label` | What kind of offer is it? | Ni irihe tangazo wakiriye? | new draft | |
| [ ] | `offerType.job` | Job | Akazi | handoff | |
| [ ] | `offerType.scholarship` | Scholarship | Buruse | handoff | |
| [ ] | `offerType.visa` | Visa | Viza | handoff | |
| [ ] | `form.label` | Offer message | Ubutumwa bw'itangazo | new draft | |
| [ ] | `form.placeholder` | Paste the WhatsApp or email offer here... | Shyira hano ubutumwa bwa WhatsApp cyangwa imeli... | handoff | |
| [ ] | `form.check` | Check Offer | Suzuma ubu butumwa | handoff | |
| [ ] | `form.checking` | Checking... | Birimo gusuzumwa... | new draft | |
| [ ] | `form.error` | We could not check this offer. Check your connection and try again. | Ntibyashobotse gusuzuma iri tangazo. Reba interineti yawe wongere ugerageze. | new draft | |
| [ ] | `upload.button` | Upload Screenshot | Shyiraho ifoto y'ubutumwa | handoff | |
| [ ] | `upload.hint` | The image is read on your phone and never uploaded. | Ifoto isomerwa kuri telefoni yawe, ntoherezwa ahandi. | new draft | |
| [ ] | `upload.reading` | Reading screenshot... | Turimo gusoma ifoto... | new draft | |
| [ ] | `upload.tooBig` | Image must be under 5 MB. | Ifoto igomba kuba munsi ya MB 5. | new draft | |
| [ ] | `upload.notImage` | Please choose an image file. | Hitamo ifoto. | new draft | |
| [ ] | `upload.noText` | No text found in this image. Try a clearer screenshot. | Nta nyandiko ibonetse kuri iyi foto. Gerageza ifoto igaragara neza. | new draft | |
| [ ] | `upload.failed` | Could not read this image. Try again or paste the text. | Ntibyashobotse gusoma iyi foto. Ongera ugerageze cyangwa wandike ubutumwa. | new draft | |
| [ ] | `risk.high_risk` | HIGH RISK | IBYAGO BYINSHI | handoff | |
| [ ] | `risk.suspicious` | MEDIUM RISK | IBYAGO BIRINGANIYE | handoff | |
| [ ] | `risk.low_risk` | LOW RISK | IBYAGO BIKE | handoff | |
| [ ] | `explain.high_risk` | It's likely a scam. Do not pay or share personal documents. | Birashoboka cyane ko ari uburiganya. Ntukishyure kandi ntutange ibyangombwa byawe. | new draft | |
| [ ] | `explain.suspicious` | Be careful. Some warning signs were found. Verify before you pay or share anything. | Witonde! Hari ibimenyetso by'uburiganya byabonetse. Banza ugenzure mbere yo kwishyura cyangwa gutanga ikintu icyo ari cyo cyose. | new draft | |
| [ ] | `explain.low_risk` | No major scam signs found. Still verify the company through official channels. | Nta bimenyetso bikomeye by'uburiganya byabonetse. Ariko banza ugenzure ikigo unyuze ku nzego zemewe. | new draft | |
| [ ] | `score` | Risk score | Urugero rw'ibyago | new draft | |
| [ ] | `flagsTitle` | Red Flags Found | Ibimenyetso by'uburiganya byabonetse | handoff | |
| [ ] | `noFlags` | No red flags found. | Nta bimenyetso by'uburiganya byabonetse. | new draft | |
| [ ] | `flags.upfront_fee` | Upfront payment requested | Barasaba kwishyura amafaranga mbere | handoff | |
| [ ] | `flags.guaranteed_outcome` | Guaranteed visa/job/scholarship claim | Baguhamiriza viza, akazi cyangwa buruse 100% | handoff | |
| [ ] | `flags.urgency_pressure` | Pressure to act quickly | Barakwihutisha ngo udatekereza | handoff | |
| [ ] | `flags.free_email_contact` | Generic email address (e.g. gmail.com) | Bakoresha imeli rusange (nka gmail.com) aho gukoresha iy'ikigo | handoff | |
| [ ] | `flags.chat_app_only` | Contact only through WhatsApp or Telegram | Bavugana nawe kuri WhatsApp cyangwa Telegram gusa | new draft | |
| [ ] | `flags.sensitive_info_request` | Asks for passport/ID/PIN up front | Basaba pasiporo, indangamuntu cyangwa PIN mbere y'igihe | handoff | |
| [ ] | `flags.blacklisted_entity` | Names a company or contact known for scams | Havugwamo ikigo cyangwa umuntu uzwiho uburiganya | new draft | |
| [ ] | `flags.flagged_entity` | Names a company or contact reported as suspicious | Havugwamo ikigo cyangwa umuntu ukekwaho uburiganya | new draft | |
| [ ] | `nextSteps` | What to do next | Icyo wakora ubu | new draft | |
| [ ] | `actions.reportRib` | Report to RIB (166) | Tanga raporo kuri RIB (166) | handoff | |
| [ ] | `actions.findAmbassador` | Find a Digital Ambassador | Shaka Umuhuzabikorwa w'Ikoranabuhanga | handoff | |
| [ ] | `actions.ambassadorTitle` | Digital Ambassadors | Abahuzabikorwa b'Ikoranabuhanga | new draft | |
| [ ] | `actions.ambassadorEmpty` | The ambassador list is coming soon. Until then, call RIB on 166 for help. | Urutonde rw'abahuzabikorwa ruzaboneka vuba. Hagati aho, hamagara RIB kuri 166 bagufashe. | new draft | |
| [ ] | `actions.close` | Close | Funga | new draft | |
| [ ] | `sms.label` | Send result to my phone | Ohereza igisubizo kuri telefoni yanjye | new draft | |
| [ ] | `sms.placeholder` | 07X XXX XXXX | 07X XXX XXXX | new draft | |
| [ ] | `sms.send` | Send | Ohereza | new draft | |
| [ ] | `sms.sending` | Sending... | Birimo koherezwa... | new draft | |
| [ ] | `sms.sent` | Sent. Check your messages. | Byoherejwe. Reba ubutumwa bwawe. | new draft | |
| [ ] | `sms.invalid` | Enter a valid Rwandan phone number. | Andika nimero ya telefoni yo mu Rwanda yemewe. | new draft | |
| [ ] | `sms.failed` | Could not send the SMS. Try again later. | Ntibyashobotse kohereza SMS. Uzongere ugerageze nyuma. | new draft | |
| [ ] | `samples.label` | Try an example: | Gerageza urugero: | new draft | |
| [ ] | `samples.job` | Job scam | Uburiganya bw'akazi | new draft | |
| [ ] | `samples.scholarship` | Scholarship scam | Uburiganya bwa buruse | new draft | |
| [ ] | `samples.visa` | Visa scam | Uburiganya bwa viza | new draft | |
| [ ] | `share.whatsapp` | Share on WhatsApp | Sangiza kuri WhatsApp | new draft | |
| [ ] | `share.copy` | Copy result | Koporora igisubizo | new draft | |
| [ ] | `share.copied` | Copied | Byakoporowe | new draft | |
| [ ] | `share.intro` | Genzura checked an offer: | Genzura yasuzumye itangazo: | new draft | |
| [ ] | `share.flags` | Red flags: | Ibimenyetso by'uburiganya: | new draft | |
| [ ] | `share.outro` | Check offers before you pay: | Suzuma amatangazo mbere yo kwishyura: | new draft | |
| [ ] | `channels.title` | Use Genzura your way | Koresha Genzura uko ubishaka | new draft | |
| [ ] | `channels.intro` | Built for every phone, from smartphones to basic feature phones. | Yagenewe telefoni zose, kuva ku zigezweho kugeza ku zisanzwe. | new draft | |
| [ ] | `channels.available` | Available now | Iraboneka ubu | new draft | |
| [ ] | `channels.soon` | Coming soon | Iraza vuba | new draft | |
| [ ] | `channels.web.title` | Website | Urubuga | new draft | |
| [ ] | `channels.web.body` | Paste a message or upload a screenshot and get a result in seconds. | Shyiramo ubutumwa cyangwa ifoto yabwo, ubone igisubizo mu masegonda. | new draft | |
| [ ] | `channels.ussd.title` | USSD | USSD | new draft | |
| [ ] | `channels.ussd.body` | Dial a short code on any phone, no internet needed, and get a verdict on screen. | Kanda kode ngufi kuri telefoni iyo ari yo yose, nta interineti ikenewe, ubone igisubizo kuri ekarani. | new draft | |
| [ ] | `channels.sms.title` | SMS | SMS | new draft | |
| [ ] | `channels.sms.body` | Receive your result as a text message you can keep and show others. | Akira igisubizo mu butumwa bugufi ushobora kubika no kwereka abandi. | new draft | |
| [ ] | `faq.title` | Frequently asked questions | Ibibazo bikunze kubazwa | new draft | |
| [ ] | `faq.items.1.q` | Is Genzura free to use? | Gukoresha Genzura ni ubuntu? | new draft | |
| [ ] | `faq.items.1.a` | Yes. Checking an offer costs nothing. | Yego. Gusuzuma itangazo nta kiguzi bisaba. | new draft | |
| [ ] | `faq.items.2.q` | What happens to my screenshot and message? | Ifoto n'ubutumwa byanjye bigenda bite? | new draft | |
| [ ] | `faq.items.2.a` | Screenshots are read on your own phone and never uploaded. The offer text is checked and stored without personal details such as phone numbers and email addresses, so authorities can see scam trends without seeing who you are. | Amafoto asomerwa kuri telefoni yawe kandi ntoherezwa ahandi. Inyandiko y'itangazo irasuzumwa ikabikwa nta makuru bwite arimo nka nimero za telefoni cyangwa imeli, kugira ngo inzego zibishinzwe zibone uko uburiganya buhagaze zitamenye uwo uri we. | new draft | |
| [ ] | `faq.items.3.q` | If the result is LOW RISK, is the offer safe? | Niba igisubizo ari IBYAGO BIKE, itangazo riba ryizewe? | new draft | |
| [ ] | `faq.items.3.a` | Not necessarily. No tool can be 100% sure. LOW RISK means no major warning signs were found. Always confirm the company through official channels before you pay or share documents. | Si ngombwa. Nta gikoresho gishobora kwizera 100%. IBYAGO BIKE bivuze ko nta bimenyetso bikomeye by'uburiganya byabonetse. Buri gihe banza ugenzure ikigo unyuze ku nzego zemewe mbere yo kwishyura cyangwa gutanga ibyangombwa. | new draft | |
| [ ] | `faq.items.4.q` | Which offers can I check? | Ni ayahe matangazo nshobora gusuzuma? | new draft | |
| [ ] | `faq.items.4.a` | Job offers, scholarships and visa offers, especially ones for opportunities abroad that you received by WhatsApp, SMS, email or social media. | Amatangazo y'akazi, buruse na viza, cyane cyane ay'amahirwe yo hanze y'igihugu wakiriye kuri WhatsApp, SMS, imeli cyangwa imbuga nkoranyambaga. | new draft | |
| [ ] | `faq.items.5.q` | I don't have a smartphone. Can I still use it? | Nta telefoni igezweho mfite. Nshobora kuyikoresha? | new draft | |
| [ ] | `faq.items.5.a` | A USSD and SMS version for basic phones is being built, so anyone can check an offer without internet. | Hari gukorwa uburyo bwa USSD na SMS kuri telefoni zisanzwe, kugira ngo buri wese abashe gusuzuma itangazo nta interineti. | new draft | |
| [ ] | `faq.items.6.q` | I already paid. What should I do? | Naramaze kwishyura. Nakora iki? | new draft | |
| [ ] | `faq.items.6.a` | Stop sending money, keep every message and receipt, and report it to the Rwanda Investigation Bureau (RIB) on 166 as soon as possible. | Hagarika kohereza amafaranga, ubike ubutumwa bwose n'inyemezabwishyu, maze utange raporo ku Rwego rw'Igihugu rw'Ubugenzacyaha (RIB) kuri 166 vuba bishoboka. | new draft | |
| [ ] | `footer.tagline` | Helping young people in Rwanda check overseas job, scholarship and visa offers before they pay. | Dufasha urubyiruko rwo mu Rwanda gusuzuma amatangazo y'akazi, buruse na viza byo hanze mbere yo kwishyura. | new draft | |
| [ ] | `footer.explore` | Explore | Ibirimo | new draft | |
| [ ] | `footer.help` | Get help | Saba ubufasha | new draft | |
| [ ] | `footer.faq` | FAQ | Ibibazo | new draft | |
| [ ] | `footer.rib` | Rwanda Investigation Bureau | Urwego rw'Igihugu rw'Ubugenzacyaha | new draft | |
| [ ] | `footer.privacy` | Your screenshots never leave your phone. Personal details are removed before anything is stored. | Amafoto yawe ntava kuri telefoni yawe. Amakuru bwite akurwamo mbere y'uko hagira ikibikwa. | new draft | |
| [ ] | `footer.rights` | All rights reserved. | Uburenganzira bwose burasigasiwe. | new draft | |
| [ ] | `footer.made` | Made in Rwanda | Byakorewe mu Rwanda | new draft | |
| [ ] | `footer.top` | Back to top | Subira hejuru | new draft | |
| [ ] | `directory.title` | Official Verification Directory | Urutonde rw'ibigo byemewe byo kugenzura amakuru | handoff | |
| [ ] | `directory.intro` | Contact these official institutions to verify information, report fraud or get support. | Vugana n'ibi bigo byemewe kugira ngo ugenzure amakuru, utange raporo y'uburiganya cyangwa ubone ubufasha. | new draft | |
| [ ] | `directory.search` | Search... | Shakisha... | new draft | |
| [ ] | `directory.verified` | Verified | Byemejwe | new draft | |
| [ ] | `directory.lastVerified` | Last verified | Byagenzuwe bwa nyuma | handoff | |
| [ ] | `directory.empty` | No institutions found. | Nta kigo kibonetse. | new draft | |

## USSD and SMS (`backend/app/messages.py`)

Keep this text short and use plain characters only: no accents, no curly quotes. `{verdict}` and `{reason}` are filled in automatically, so do not translate them.

| OK | Key | English | Kinyarwanda | Correction |
|---|---|---|---|---|
| [ ] | `main_menu` | Genzura scam check / 1. Job offer / 2. Scholarship / 3. Visa | Genzura: suzuma uburiganya / 1. Akazi / 2. Buruse / 3. Viza | |
| [ ] | `ask_message` | Type the message you received: | Andika ubutumwa wakiriye: | |
| [ ] | `invalid` | Invalid choice. Please dial again. | Ibyo wahisemo si byo. Ongera uhamagare. | |
| [ ] | `about` | Genzura checks overseas job, scholarship and visa offers for scams. | Genzura isuzuma amatangazo y'akazi, buruse na viza byo hanze ngo wirinde uburiganya. | |
| [ ] | `no_flags` | No red flags found | Nta bimenyetso byabonetse | |
| [ ] | `ussd_result` | {verdict} / Reason: {reason} / Call RIB 166 to verify. | {verdict} / Impamvu: {reason} / Hamagara RIB 166 ugenzure. | |
| [ ] | `sms_result` | Genzura: {verdict} Reason: {reason}. Call RIB 166 to verify. | Genzura: {verdict} Impamvu: {reason}. Hamagara RIB 166. | |
| [ ] | `verdict.high_risk` | HIGH RISK: likely a scam. Do not pay. | IBYAGO BYINSHI: birashoboka ko ari uburiganya. Ntukishyure. | |
| [ ] | `verdict.suspicious` | MEDIUM RISK: be careful. Do not pay or share documents. | IBYAGO BIRINGANIYE: witonde. Ntukishyure, ntutange ibyangombwa. | |
| [ ] | `verdict.low_risk` | LOW RISK: no major scam signs. Still verify. | IBYAGO BIKE: nta bimenyetso bikomeye. Banza ugenzure. | |
| [ ] | `flags.upfront_fee` | Upfront payment requested | Basaba kwishyura mbere | |
| [ ] | `flags.guaranteed_outcome` | Guaranteed outcome claim | Bakwizeza ibitangaza 100% | |
| [ ] | `flags.urgency_pressure` | Pressure to act fast | Barakwihutisha | |
| [ ] | `flags.free_email_contact` | Generic email address | Imeli rusange (nka gmail) | |
| [ ] | `flags.chat_app_only` | WhatsApp/Telegram only | WhatsApp/Telegram gusa | |
| [ ] | `flags.sensitive_info_request` | Asks for passport/ID/PIN | Basaba pasiporo/ID/PIN | |
| [ ] | `flags.blacklisted_entity` | Known scam company | Ikigo kizwiho uburiganya | |
| [ ] | `flags.flagged_entity` | Suspicious company | Ikigo gikekwaho uburiganya | |

Reviewer name: Didier Date: 11/1/2026
