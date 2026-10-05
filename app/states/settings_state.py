import reflex as rx

import json
import logging
from typing import Any

SETTINGS_KEY = "voicemate.settings.v1"
DEFAULT_SETTINGS = {"theme": "light", "language": "en", "speech": "en-US"}

TRANSLATIONS: dict[str, str] = {
    "notes": "नोट्स",
    "Home": "होम",
    "My notes": "मेरे नोट्स",
    "Favorites": "पसंदीदा",
    "Capture": "आवाज़",
    "New note": "नया नोट",
    "Settings": "सेटिंग्स",
    "Import audio": "ऑडियो आयात",
    "A little space for your mind": "आपके विचारों के लिए एक छोटी जगह",
    "Your personal notebook": "आपकी निजी नोटबुक",
    "Opening your notebook…": "आपकी नोटबुक खुल रही है…",
    "YOUR PERSONAL SPACE": "आपकी निजी जगह",
    "A clearer mind starts here.": "साफ़ सोच की शुरुआत यहाँ से।",
    "Catch a thought. Keep what matters. Come back to it.": "विचार लिखें। ज़रूरी बातें रखें। फिर लौटें।",
    "One thought at a time": "एक समय में एक विचार",
    "Make room for\nyour next idea.": "अपने अगले विचार के लिए\nजगह बनाएँ।",
    "No perfect words needed. Just a quiet place to begin.": "सटीक शब्द ज़रूरी नहीं। बस शुरुआत के लिए एक शांत जगह।",
    "Create a text note": "लिखित नोट बनाएँ",
    "Capture a spoken thought": "बोलकर विचार दर्ज करें",
    "Pick up where you left off": "जहाँ छोड़ा था, वहीं से शुरू करें",
    "All notes": "सभी नोट्स",
    "A place for every thought": "हर विचार के लिए जगह",
    "A thought worth keeping": "सहेजने योग्य विचार",
    "YOUR NOTEBOOK": "आपकी नोटबुक",
    "Keep your favorites close.": "पसंदीदा विचार पास रखें।",
    "Every thought, in one place.": "सभी विचार, एक जगह।",
    "The ideas you want to come back to, collected here.": "जिन विचारों पर लौटना है, वे यहाँ हैं।",
    "Find a thought, revisit an idea, or start something new.": "विचार खोजें, दोबारा पढ़ें या कुछ नया शुरू करें।",
    "Search titles and note text…": "शीर्षक और नोट में खोजें…",
    "Clear filters": "फ़िल्टर हटाएँ",
    "Load more": "और दिखाएँ",
    "Recently updated": "हाल में बदले गए",
    "Newest created": "नए बनाए गए",
    "Oldest updated": "पुराने बदलाव",
    "Title A–Z": "शीर्षक A–Z",
    "Personal": "निजी",
    "Work": "काम",
    "Learning": "पढ़ाई",
    "Ideas": "विचार",
    "Note title": "नोट का शीर्षक",
    "Favorite": "पसंदीदा",
    "Category": "श्रेणी",
    "Give this thought a name…": "इस विचार को नाम दें…",
    "Note text / transcript": "नोट / प्रतिलेख",
    "Editable · plain text": "संपादन योग्य · सादा पाठ",
    "What's on your mind?\n\nWrite freely. This space is yours.": "आप क्या सोच रहे हैं?\n\nखुलकर लिखें। यह आपकी जगह है।",
    "Changes are saved only when you tap Save note.": "बदलाव केवल ‘नोट सहेजें’ दबाने पर सहेजे जाते हैं।",
    "Saving…": "सहेजा जा रहा है…",
    "Save note": "नोट सहेजें",
    "Back to notes": "नोट्स पर वापस",
    "This note isn't here": "यह नोट यहाँ नहीं है",
    "It may have been deleted, or saved in a different browser.": "यह मिट गया होगा या दूसरे ब्राउज़र में सहेजा होगा।",
    "Return to notes": "नोट्स पर लौटें",
    "A SPACE TO THINK": "सोचने की जगह",
    "Start with a thought.": "एक विचार से शुरू करें।",
    "Make this thought your own.": "इस विचार को अपना बनाएँ।",
    "Write, revisit, and refine. You're in no rush.": "लिखें, लौटें और सुधारें। कोई जल्दी नहीं।",
    "Delete": "मिटाएँ",
    "Save your note to unlock the optional AI assistant.": "वैकल्पिक AI सहायक के लिए नोट सहेजें।",
    "Your next thought belongs here": "आपका अगला विचार यहाँ लिखें",
    "Write your first note": "अपना पहला नोट लिखें",
    "A space for your favorites": "पसंदीदा विचारों की जगह",
    "No notes found": "कोई नोट नहीं मिला",
    "Reset filters": "फ़िल्टर रीसेट करें",
    "Browse notes": "नोट्स देखें",
    "Speech language": "बोलने की भाषा",
    "Start": "शुरू करें",
    "Stop": "रोकें",
    "Cancel session": "सत्र रद्द करें",
    "Checking browser speech support…": "ब्राउज़र का आवाज़ समर्थन जाँचा जा रहा है…",
    "Create a text note instead": "इसके बजाय लिखित नोट बनाएँ",
    "Your words, ready to refine": "आपके शब्द, सुधारने के लिए तैयार",
    "Live text · lighter words are tentative. Edit after capture ends.": "लाइव पाठ · हल्के शब्द अस्थायी हैं। बोलना समाप्त होने पर संपादित करें।",
    "Final transcript · editable after stopping": "अंतिम प्रतिलेख · रुकने के बाद संपादन योग्य",
    "Recognized words will appear here. You can also type and correct them before saving.": "पहचाने गए शब्द यहाँ आएँगे। सहेजने से पहले लिखकर सुधारें।",
    "Transcript saved and verified in this browser.": "प्रतिलेख इस ब्राउज़र में सहेजा और सत्यापित हुआ।",
    "Open saved note": "सहेजा नोट खोलें",
    "Save transcript as note": "प्रतिलेख को नोट की तरह सहेजें",
    "A LITTLE SPACE TO SPEAK": "बोलने के लिए छोटी जगह",
    "Speak a thought. Keep the words.": "विचार बोलें। शब्द सहेजें।",
    "Browser speech capture · English or Hindi · no audio files stored": "ब्राउज़र आवाज़ पहचान · अंग्रेज़ी या हिन्दी · ऑडियो फ़ाइलें सहेजी नहीं जातीं",
    "Ready when you are": "जब आप तैयार हों",
    "Waiting for microphone / speech service…": "माइक्रोफ़ोन / आवाज़ सेवा की प्रतीक्षा…",
    "Listening…": "सुना जा रहा है…",
    "Finishing recognized words…": "पहचाने शब्द पूरे किए जा रहे हैं…",
    "Capture complete · review your text": "आवाज़ दर्ज हुई · पाठ जाँचें",
    "Capture unavailable or interrupted": "आवाज़ पहचान अनुपलब्ध या बाधित",
    "Session discarded": "सत्र हटा दिया गया",
    "Checking your browser…": "ब्राउज़र जाँचा जा रहा है…",
    "Delete this note?": "यह नोट मिटाएँ?",
    "Keep note": "नोट रखें",
    "Delete note": "नोट मिटाएँ",
    "Keep your thoughts safe": "अपने विचार सुरक्षित रखें",
    "Discard & leave": "बदलाव छोड़कर जाएँ",
    "Keep editing": "संपादन जारी रखें",
    "You have unsaved changes. Stay here to save them, or leave and discard your changes.": "बदलाव सहेजे नहीं हैं। सहेजने के लिए यहीं रहें या बदलाव छोड़कर जाएँ।",
    "This removes the note and its attached AI results from this browser. You can't undo this action.": "नोट और उससे जुड़े AI परिणाम इस ब्राउज़र से मिटेंगे। इसे वापस नहीं किया जा सकता।",
    "Saved in this browser": "इस ब्राउज़र में सहेजा गया",
    "Saving to this browser…": "इस ब्राउज़र में सहेजा जा रहा है…",
    "Note deleted": "नोट मिट गया",
    "A little help with your thoughts": "आपके विचारों के लिए थोड़ी मदद",
    "AI assistant · optional, with your permission": "AI सहायक · वैकल्पिक, आपकी अनुमति से",
    "What would help?": "किस मदद की ज़रूरत है?",
    "Translation target": "अनुवाद की भाषा",
    "Question (for Ask this note only)": "प्रश्न (केवल इस नोट से पूछने के लिए)",
    "What does this note say about…?": "यह नोट किस बारे में बताता है…?",
    "Working…": "काम जारी है…",
    "Review AI request": "AI अनुरोध की समीक्षा करें",
    "Summarize": "सारांश",
    "Key points": "मुख्य बिंदु",
    "Suggest title": "शीर्षक सुझाएँ",
    "Action items": "कार्य सूची",
    "Study questions": "अध्ययन प्रश्न",
    "Simplify": "सरल करें",
    "Translate": "अनुवाद",
    "Ask this note": "इस नोट से पूछें",
    "Editable AI result": "संपादन योग्य AI परिणाम",
    "Copy current text": "वर्तमान पाठ कॉपी करें",
    "Save result": "परिणाम सहेजें",
    "Send this saved note to AI?": "यह सहेजा नोट AI को भेजें?",
    "Don't send": "न भेजें",
    "I agree · Send to AI": "मैं सहमत हूँ · AI को भेजें",
    "Retry · review permission": "फिर कोशिश करें · अनुमति जाँचें",
    "Attached results": "जुड़े परिणाम",
    "Result copied": "परिणाम कॉपी हुआ",
    "Saved version only · unsaved editor changes are not included.": "केवल सहेजा संस्करण · बिना सहेजे संपादन शामिल नहीं हैं।",
    "Copy note": "नोट कॉपी करें",
    "Download text": "पाठ डाउनलोड करें",
    "Share note": "नोट साझा करें",
    "Copy instead": "इसके बजाय कॉपी करें",
    "Dismiss": "बंद करें",
    "Note copied": "नोट कॉपी हुआ",
    "Note shared": "नोट साझा हुआ",
    "Share cancelled": "साझा करना रद्द हुआ",
    "Sharing unavailable. Choose Copy instead if you want to use the clipboard.": "साझा करना उपलब्ध नहीं। क्लिपबोर्ड के लिए ‘इसके बजाय कॉपी करें’ चुनें।",
    "Clipboard unavailable. Select the saved note text and copy manually.": "क्लिपबोर्ड उपलब्ध नहीं। सहेजे नोट का पाठ चुनकर कॉपी करें।",
    "Appearance": "रूप",
    "Light": "हल्का",
    "Dark": "गहरा",
    "Interface language": "इंटरफ़ेस भाषा",
    "Default speech language": "बोलने की डिफ़ॉल्ट भाषा",
    "Save preferences": "पसंद सहेजें",
    "Preferences saved and verified": "पसंद सहेजी और सत्यापित हुई",
    "Preferences could not be saved. Check browser storage and retry.": "पसंद सहेजी नहीं गई। ब्राउज़र संग्रहण जाँचकर फिर प्रयास करें।",
    "Invalid preferences. Choose the listed options.": "अमान्य पसंद। दिए गए विकल्प चुनें।",
    "Privacy & help": "गोपनीयता और सहायता",
    "Clear all notes and AI results": "सभी नोट्स और AI परिणाम मिटाएँ",
    "Clear this browser notebook?": "इस ब्राउज़र की नोटबुक मिटाएँ?",
    "Cancel": "रद्द करें",
    "Yes, clear everything": "हाँ, सब मिटाएँ",
    "Clearing…": "मिटाया जा रहा है…",
    "All notes and AI results cleared and verified": "सभी नोट्स और AI परिणाम मिटाए और सत्यापित हुए",
    "Clear failed or could not be verified. Some data may remain. Retry before leaving this page.": "मिटाना विफल या सत्यापन नहीं हुआ। कुछ डेटा बचा हो सकता है। जाने से पहले फिर प्रयास करें।",
    "Wait for saving or AI processing to finish before clearing.": "मिटाने से पहले सहेजना या AI प्रक्रिया समाप्त होने दें।",
    "Choose an audio file": "ऑडियो फ़ाइल चुनें",
    "MP3, M4A, WAV, WebM or MP4 · maximum 20 MB": "MP3, M4A, WAV, WebM या MP4 · अधिकतम 20 MB",
    "Selection stays in your browser until you explicitly agree and send.": "जब तक आप सहमत होकर भेजते नहीं, चुनी फ़ाइल ब्राउज़र में रहती है।",
    "I consent to send this audio for transcription": "मैं प्रतिलेखन के लिए यह ऑडियो भेजने की सहमति देता/देती हूँ",
    "Send audio & transcribe": "ऑडियो भेजें और प्रतिलेखन करें",
    "Transcribing…": "प्रतिलेखन जारी है…",
    "Clear selection": "चयन हटाएँ",
    "Review transcript": "प्रतिलेख जाँचें",
    "Editable transcript": "संपादन योग्य प्रतिलेख",
    "Transcription received. Review and correct before saving.": "प्रतिलेख मिला। सहेजने से पहले जाँचें और सुधारें।",
    "Choose one supported nonempty audio file up to 20 MB.": "20 MB तक की एक समर्थित, खाली न होने वाली ऑडियो फ़ाइल चुनें।",
    "Audio transcription is not enabled for this provider. You can still type a note or use browser speech capture.": "इस प्रदाता के लिए ऑडियो प्रतिलेखन सक्षम नहीं है। आप नोट लिख सकते हैं या ब्राउज़र आवाज़ पहचान इस्तेमाल कर सकते हैं।",
    "Transcription is not configured. Text notes and browser speech capture remain available.": "प्रतिलेखन कॉन्फ़िगर नहीं है। लिखित नोट्स और ब्राउज़र आवाज़ पहचान उपलब्ध हैं।",
    "Explicit audio consent is required. Nothing was sent to the provider.": "ऑडियो भेजने की स्पष्ट सहमति ज़रूरी है। प्रदाता को कुछ नहीं भेजा गया।",
    "No usable transcript was returned. Nothing was saved.": "उपयोग योग्य प्रतिलेख नहीं मिला। कुछ सहेजा नहीं गया।",
    "The provider has insufficient credits for transcription. Retry only after credits are restored.": "प्रतिलेखन के लिए प्रदाता के क्रेडिट पर्याप्त नहीं हैं। क्रेडिट मिलने पर फिर प्रयास करें।",
    "Transcription is rate limited. Wait before consenting to retry.": "प्रतिलेखन की अनुरोध सीमा पूरी हुई। फिर अनुमति देने से पहले प्रतीक्षा करें।",
    "Transcription timed out. Review consent before retrying.": "प्रतिलेखन का समय समाप्त हुआ। फिर प्रयास से पहले अनुमति जाँचें।",
    "The transcription service cannot be reached. Check connectivity and retry.": "प्रतिलेखन सेवा तक पहुँचा नहीं जा सका। कनेक्शन जाँचकर फिर प्रयास करें।",
    "The provider does not support this transcription request. No transcript was saved.": "प्रदाता यह प्रतिलेखन अनुरोध समर्थित नहीं करता। प्रतिलेख सहेजा नहीं गया।",
    "Audio import failed. Nothing was saved. Select your file and consent again to retry.": "ऑडियो आयात विफल। कुछ सहेजा नहीं गया। फिर फ़ाइल चुनें और सहमति दें।",
    "Add some transcript text before saving.": "सहेजने से पहले कुछ प्रतिलेख लिखें।",
    "Add recognized words or edit the transcript before saving.": "सहेजने से पहले पहचाने शब्द जोड़ें या प्रतिलेख संपादित करें।",
    "Save this note successfully before exporting.": "निर्यात से पहले इस नोट को सफलतापूर्वक सहेजें।",
    "Download requested · check your browser downloads.": "डाउनलोड का अनुरोध हुआ · ब्राउज़र डाउनलोड जाँचें।",
    "Your saved notebook couldn't be read.": "आपकी सहेजी नोटबुक पढ़ी नहीं जा सकी।",
    "Stored notes couldn't be read. Nothing has been overwritten.": "सहेजे नोट्स पढ़े नहीं जा सके। कुछ बदला नहीं गया।",
    "Add a title or some text before saving your note.": "सहेजने से पहले शीर्षक या कुछ पाठ जोड़ें।",
    "Choose a valid category.": "मान्य श्रेणी चुनें।",
    "Use a title under 160 characters and note text under 100,000 characters.": "शीर्षक 160 अक्षरों और नोट पाठ 100,000 अक्षरों की सीमा में रखें।",
    "We couldn't confirm the save in this browser. Keep this page open and try again. Check that browser storage is enabled and has space.": "इस ब्राउज़र में सहेजना सत्यापित नहीं हुआ। पेज खुला रखकर फिर कोशिश करें। ब्राउज़र संग्रहण और उपलब्ध जगह जाँचें।",
    "Deletion couldn't be saved in this browser. Your note has been kept.": "इस ब्राउज़र में मिटाना सहेजा नहीं जा सका। आपका नोट रखा गया है।",
    "Couldn't delete this note. Reload and try again.": "नोट मिटाया नहीं जा सका। फिर लोड करके कोशिश करें।",
    "Couldn't update this note. Reload and try again.": "नोट बदला नहीं जा सका। फिर लोड करके कोशिश करें।",
    "Microphone permission was denied. Allow microphone access in your browser's site settings, then try again.": "माइक्रोफ़ोन अनुमति नहीं मिली। ब्राउज़र साइट सेटिंग्स में अनुमति दें और फिर कोशिश करें।",
    "This browser's speech service is unavailable or blocked. Try another supported browser or type your note instead.": "ब्राउज़र आवाज़ सेवा अनुपलब्ध या अवरुद्ध है। दूसरा समर्थित ब्राउज़र चुनें या नोट लिखें।",
    "No working microphone was found. Check your microphone and browser settings.": "काम करने वाला माइक्रोफ़ोन नहीं मिला। माइक्रोफ़ोन और ब्राउज़र सेटिंग्स जाँचें।",
    "The browser's speech service couldn't be reached. Check your connection and try again.": "ब्राउज़र आवाज़ सेवा से संपर्क नहीं हुआ। कनेक्शन जाँचकर फिर कोशिश करें।",
    "No speech was recognized. Try again and speak clearly after listening starts.": "आवाज़ पहचानी नहीं गई। सुनना शुरू होने पर स्पष्ट बोलकर फिर कोशिश करें।",
    "Speech capture was interrupted. Any final recognized words have been kept.": "आवाज़ पहचान बाधित हुई। अंतिम पहचाने शब्द रखे गए हैं।",
    "Capture stopped because this page was hidden. Any final recognized words have been kept.": "पेज छिपने के कारण आवाज़ पहचान रुकी। अंतिम शब्द रखे गए हैं।",
    "This browser's speech service doesn't support the selected language. Try the other language or another browser.": "ब्राउज़र आवाज़ सेवा चुनी भाषा समर्थित नहीं करती। दूसरी भाषा या ब्राउज़र चुनें।",
    "Speech recognition isn't available in this browser. Try a browser with Web Speech support, or create a text note.": "इस ब्राउज़र में आवाज़ पहचान नहीं है। Web Speech समर्थित ब्राउज़र या लिखित नोट चुनें।",
    "Microphone capture needs a secure HTTPS page (or localhost). Open this app securely to try again.": "माइक्रोफ़ोन के लिए सुरक्षित HTTPS पेज (या localhost) चाहिए। ऐप सुरक्षित रूप से खोलें।",
    "Speech capture couldn't start. Check your microphone and browser speech service, then retry.": "आवाज़ पहचान शुरू नहीं हुई। माइक्रोफ़ोन और ब्राउज़र आवाज़ सेवा जाँचकर फिर कोशिश करें।",
    "Speech recognition stopped unexpectedly. Any final recognized words have been kept. Try again or edit the text below.": "आवाज़ पहचान अचानक रुकी। अंतिम शब्द रखे गए हैं। फिर कोशिश करें या नीचे पाठ संपादित करें।",
    "Save this note successfully before using AI.": "AI इस्तेमाल करने से पहले नोट सफलतापूर्वक सहेजें।",
    "The AI provider has insufficient credits. The server owner needs to replenish credits before you retry. Your notes and existing results are safe.": "AI प्रदाता के क्रेडिट पर्याप्त नहीं हैं। फिर कोशिश से पहले सेवा संचालक को क्रेडिट जोड़ने होंगे। आपके नोट्स और पुराने परिणाम सुरक्षित हैं।",
    "AI is not configured on the server. You can still write and save notes locally.": "सर्वर पर AI कॉन्फ़िगर नहीं है। आप फिर भी नोट लिख और सहेज सकते हैं।",
    "The AI provider is busy or rate limited. Wait a minute, then retry.": "AI प्रदाता व्यस्त है या अनुरोध सीमा पूरी है। एक मिनट रुककर कोशिश करें।",
    "This browser is offline. Reconnect and retry. No note text was sent to the AI provider.": "ब्राउज़र ऑफ़लाइन है। कनेक्ट होकर फिर कोशिश करें। नोट पाठ AI प्रदाता को नहीं भेजा गया।",
    "AI took too long to respond. Nothing was generated or saved. Please retry.": "AI का जवाब देर से आया। कुछ बनाया या सहेजा नहीं गया। फिर कोशिश करें।",
    "The server cannot reach the AI provider. Check connectivity and retry; local notes still work.": "सर्वर AI प्रदाता से संपर्क नहीं कर सका। कनेक्शन जाँचें; स्थानीय नोट्स उपलब्ध हैं।",
    "The AI provider rejected the server configuration. The server owner must fix it; local notes still work.": "AI प्रदाता ने सेवा कॉन्फ़िगरेशन अस्वीकार किया। संचालक को इसे ठीक करना होगा; नोट्स उपलब्ध हैं।",
    "The AI provider could not complete this request. Please try again later.": "AI प्रदाता अनुरोध पूरा नहीं कर सका। बाद में कोशिश करें।",
    "No new result was generated.": "कोई नया परिणाम नहीं बना।",
    "Sending the saved note you approved…": "आपका स्वीकृत सहेजा नोट भेजा जा रहा है…",
    "Saving result to this browser…": "परिणाम इस ब्राउज़र में सहेजा जा रहा है…",
    "Result saved in this browser · original note unchanged": "परिणाम ब्राउज़र में सहेजा गया · मूल नोट नहीं बदला",
    "Result not saved": "परिणाम सहेजा नहीं गया",
    "Clipboard unavailable. Select the result text and copy it manually.": "क्लिपबोर्ड उपलब्ध नहीं। परिणाम का पाठ चुनकर स्वयं कॉपी करें।",
    "Browser storage could not be confirmed. Copy the result or retry Save result. Keep this page open; unsaved results will otherwise be lost.": "ब्राउज़र संग्रहण सत्यापित नहीं हुआ। परिणाम कॉपी करें या फिर सहेजें। पेज खुला रखें; बिना सहेजा परिणाम खो सकता है।",
    "Uses only your last saved transcript, not unsaved edits. Maximum 20,000 characters. Results never replace your original note.": "केवल अंतिम सहेजा प्रतिलेख इस्तेमाल होता है, बिना सहेजे बदलाव नहीं। अधिकतम 20,000 अक्षर। परिणाम मूल नोट को नहीं बदलते।",
    "If you confirm, the full original saved transcript and your question (if provided) will be sent through this app's server to its configured external OpenAI-compatible AI provider. This is not on-device processing. The provider may process or retain your text under its own privacy policies. Do not send confidential or sensitive information.": "सहमति पर पूरा मूल सहेजा प्रतिलेख और आपका प्रश्न (यदि दिया हो) ऐप के सर्वर से बाहरी OpenAI-संगत AI प्रदाता को जाएगा। यह डिवाइस पर प्रक्रिया नहीं है। प्रदाता अपनी गोपनीयता नीति के अनुसार पाठ रख या संसाधित कर सकता है। गोपनीय या संवेदनशील जानकारी न भेजें।",
    "Only this request is approved. Retrying requires a fresh confirmation. Your transcript will not be overwritten. No provider call has happened yet.": "केवल इस अनुरोध की अनुमति है। फिर कोशिश के लिए नई सहमति चाहिए। आपका प्रतिलेख नहीं बदला जाएगा। अभी प्रदाता को कॉल नहीं हुई है।",
    "The last provider check reported insufficient credits. AI may remain unavailable until credits are replenished. No successful connection is assumed; your local notes and recording still work.": "पिछली प्रदाता जाँच में क्रेडिट पर्याप्त नहीं थे। क्रेडिट मिलने तक AI अनुपलब्ध हो सकता है। सफल संपर्क का दावा नहीं है; नोट्स और आवाज़ पहचान उपलब्ध हैं।",
    "Start requests microphone access. Stop waits for final words; tentative words may not be finalized by the speech service. Start again to append more. Cancel discards all text in this capture session.": "शुरू करने पर माइक्रोफ़ोन की अनुमति माँगी जाती है। रोकने पर अंतिम शब्दों की प्रतीक्षा होती है; अस्थायी शब्द अंतिम न बन सकें। और जोड़ने के लिए फिर शुरू करें। रद्द करने पर इस सत्र का सारा पाठ हटता है।",
    "Only text is saved, never an audio recording. Keep this page open if saving fails; your editable transcript stays here for retry. Leaving this page discards unsaved capture text.": "केवल पाठ सहेजता है, ऑडियो रिकॉर्डिंग नहीं। सहेजना विफल हो तो पेज खुला रखें; प्रतिलेख फिर कोशिश के लिए रहेगा। पेज छोड़ने पर बिना सहेजा पाठ खोता है।",
    "Your browser may send speech to its own recognition service, which may need internet access. VoiceMate receives recognized text to power this workspace. Language support and accuracy depend on your browser and speech service.": "ब्राउज़र आवाज़ अपनी पहचान सेवा को भेज सकता है, जिसे इंटरनेट चाहिए हो सकता है। कार्यक्षेत्र चलाने के लिए VoiceMate पहचाना पाठ प्राप्त करता है। भाषा समर्थन और सटीकता ब्राउज़र व आवाज़ सेवा पर निर्भर हैं।",
    "A passing idea, a lesson learned, a plan for tomorrow. Start with a few words and make it your own.": "एक विचार, सीखी बात या कल की योजना। कुछ शब्दों से शुरू करें और अपना बनाएँ।",
    "Star a note to keep it close. If you've already starred notes, try changing your filters.": "नोट पास रखने के लिए तारा लगाएँ। पहले से तारा लगाया हो तो फ़िल्टर बदलें।",
    "Try another word or category. Your next idea might be a new note.": "दूसरा शब्द या श्रेणी चुनें। अगले विचार का नया नोट बनाएँ।",
}


def decode_settings(raw: str) -> dict[str, str]:
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != set(DEFAULT_SETTINGS):
        raise ValueError("Invalid preferences. Choose the listed options.")
    if (
        data["theme"] not in ("light", "dark")
        or data["language"] not in ("en", "hi")
        or data["speech"] not in ("en-US", "hi-IN")
    ):
        raise ValueError("Invalid preferences. Choose the listed options.")
    return data


def clear_verified(raw: str) -> bool:
    try:
        data = json.loads(raw)
        return data == {"notes": "[]", "results": "[]"}
    except (ValueError, TypeError):
        return False


class SettingsState(rx.State):
    stored_preferences: str = rx.LocalStorage(
        json.dumps(DEFAULT_SETTINGS), name=SETTINGS_KEY, sync=True
    )
    feedback: str = ""
    error: str = ""
    confirming: bool = False
    clearing: bool = False
    saving: bool = False
    _expected: str = ""
    _previous: str = ""

    @rx.var
    def preferences(self) -> dict[str, str]:
        try:
            return decode_settings(self.stored_preferences)
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            return DEFAULT_SETTINGS.copy()

    @rx.var
    def language(self) -> str:
        return self.preferences["language"]

    @rx.var
    def theme(self) -> str:
        return self.preferences["theme"]

    @rx.var
    def labels(self) -> dict[str, str]:
        return TRANSLATIONS if self.language == "hi" else {}

    @rx.event
    async def load_settings(self):
        from app.states.notes_state import NotesState

        notes = await self.get_state(NotesState)
        notes._load()
        notes.view = "settings"
        self.confirming = False
        self.feedback = ""
        self.error = ""
        try:
            decode_settings(self.stored_preferences)
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            self.error = "Invalid preferences. Choose the listed options."

    @rx.event
    def save_preferences(self, form_data: dict[str, Any]):
        if self.saving:
            return
        try:
            raw = json.dumps(
                {k: str(form_data.get(k, "")) for k in DEFAULT_SETTINGS},
                ensure_ascii=False,
            )
            decode_settings(raw)
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            self.error = "Invalid preferences. Choose the listed options."
            return
        self._previous = self.stored_preferences
        self._expected = raw
        self.stored_preferences = raw
        self.saving = True
        self.error = ""
        self.feedback = ""
        yield
        yield rx.call_script(
            "(() => { try { return localStorage.getItem('voicemate.settings.v1') || ''; } catch (_) { return ''; } })()",
            callback=SettingsState.verify_preferences,
        )

    @rx.event
    def verify_preferences(self, raw: str):
        if not self.saving:
            return
        self.saving = False
        if raw == self._expected:
            self.feedback = "Preferences saved and verified"
        else:
            self.stored_preferences = self._previous
            self.error = "Preferences could not be saved. Check browser storage and retry."

    @rx.event
    def request_clear(self):
        self.confirming = True
        self.error = ""
        self.feedback = ""

    @rx.event
    def cancel_clear(self):
        self.confirming = False

    @rx.event
    async def clear_all(self):
        from app.states.notes_state import NotesState
        from app.states.ai_state import AIState
        from app.states.import_state import ImportState

        notes = await self.get_state(NotesState)
        ai = await self.get_state(AIState)
        importing = await self.get_state(ImportState)
        if not self.confirming or self.clearing:
            return
        if notes.saving or ai.busy or ai.storing or importing.busy:
            self.error = (
                "Wait for saving or AI processing to finish before clearing."
            )
            return
        self.clearing = True
        yield
        yield rx.call_script(
            "(() => { try { localStorage.setItem('voicemate.notes.v1', '[]'); localStorage.setItem('voicemate.ai-results.v1', '[]'); return JSON.stringify({notes: localStorage.getItem('voicemate.notes.v1'), results: localStorage.getItem('voicemate.ai-results.v1')}); } catch (_) { return ''; } })()",
            callback=SettingsState.verify_clear,
        )

    @rx.event
    async def verify_clear(self, raw: str):
        if not self.clearing:
            return
        self.clearing = False
        if not clear_verified(raw):
            self.error = "Clear failed or could not be verified. Some data may remain. Retry before leaving this page."
            return
        from app.states.notes_state import NotesState
        from app.states.ai_state import AIState
        from app.states.import_state import ImportState
        from app.states.record_state import RecordState

        notes = await self.get_state(NotesState)
        ai = await self.get_state(AIState)
        importing = await self.get_state(ImportState)
        recording = await self.get_state(RecordState)
        notes.stored_notes = "[]"
        notes.editing_id = notes.draft_title = notes.draft_content = ""
        notes.capture_saved_id = notes.delete_id = ""
        notes._expected_raw = notes._previous_raw = "[]"
        notes.feedback = notes.error = ""
        notes.editor_key += 1
        ai.stored_results = "[]"
        ai.unsaved = []
        ai.context_id = ai._approved_text = ai._approved_note_id = ""
        ai.confirmation = False
        ai.feedback = ai.error = ""
        importing.transcript = ""
        importing.revision += 1
        recording.transcript = recording.interim = ""
        importing.token = ""
        importing.error = importing.feedback = ""
        self.error = ""
        self.confirming = False
        self.feedback = "All notes and AI results cleared and verified"
        yield
        yield rx.call_script(
            "(() => { try { return JSON.stringify({notes: localStorage.getItem('voicemate.notes.v1'), results: localStorage.getItem('voicemate.ai-results.v1')}); } catch (_) { return ''; } })()",
            callback=SettingsState.verify_clear_final,
        )

    @rx.event
    def verify_clear_final(self, raw: str):
        if not clear_verified(raw):
            self.feedback = ""
            self.error = "Clear failed or could not be verified. Some data may remain. Retry before leaving this page."
            self.confirming = True
