import '../../core/local_engine/local_store.dart';

/// English and Hindi for the School pages and the phone apps (TA-9, SA).
///
/// The English text is the key, so a string with no Hindi yet still reads
/// correctly. The choice is per device (a shared family phone keeps its
/// own), set from the School page's language button.
const _key = 'ui_language';

bool get uiHindi {
  try {
    return LocalStore.instance.box.get(_key) == 'hi';
  } catch (_) {
    // not-a-failure: before the local store opens (tests, first frame) the language is English
    return false;
  }
}

void setUiLanguage(String code) => LocalStore.instance.box.put(_key, code);

String tr(String en) => uiHindi ? (_hi[en] ?? en) : en;

const _hi = <String, String>{
  // the School page and its tiles
  'School': 'विद्यालय',
  'Notifications': 'सूचनाएँ',
  'Your inbox, quiet hours and alerts': 'आपकी सूचनाएँ, शांत समय और चेतावनियाँ',
  'My homework': 'मेरा गृहकार्य',
  'Due work, answers and marks': 'जमा करने का काम, उत्तर और अंक',
  'My progress': 'मेरी प्रगति',
  'Subjects, chapters and what to revise': 'विषय, अध्याय और क्या दोहराना है',
  'My exams': 'मेरी परीक्षाएँ',
  'Your datesheet': 'आपकी डेटशीट',
  'My children': 'मेरे बच्चे',
  'Timetable, homework, progress and consent': 'समय-सारणी, गृहकार्य, प्रगति और सहमति',
  'Attendance & cover': 'उपस्थिति और स्थानापन्न',
  'Mark absences, leave and substitutions': 'अनुपस्थिति, छुट्टी और स्थानापन्न',
  'Homework': 'गृहकार्य',
  'Set, mark and follow up': 'दें, जाँचें और पूछें',
  'Class progress': 'कक्षा की प्रगति',
  'Mastery by section and chapter': 'कक्षा और अध्याय के अनुसार दक्षता',
  'Your sections, and who needs help': 'आपकी कक्षाएँ, और किसे मदद चाहिए',
  'Exams': 'परीक्षाएँ',
  'Datesheets and invigilation': 'डेटशीट और निरीक्षण',
  'Paper reviews': 'प्रश्नपत्र समीक्षा',
  'Papers waiting for review or approval': 'समीक्षा या स्वीकृति के लिए प्रश्नपत्र',
  'Papers others asked you to review': 'जिन प्रश्नपत्रों की समीक्षा आपसे माँगी गई',
  'Import & export': 'आयात और निर्यात',
  'Sections, people, allocations, holidays': 'कक्षाएँ, लोग, आवंटन, छुट्टियाँ',
  'API keys': 'API कुंजियाँ',
  'Question bank API access': 'प्रश्न बैंक API पहुँच',
  'Staff permissions': 'स्टाफ़ अनुमतियाँ',
  'Make a teacher an admin for one area': 'किसी शिक्षक को एक क्षेत्र का व्यवस्थापक बनाएँ',
  'My day': 'मेरा दिन',
  'Periods, duties and check-in': 'पीरियड, ड्यूटी और उपस्थिति',
  'My exam duties': 'मेरी परीक्षा ड्यूटी',
  'Invigilation roster': 'निरीक्षण सूची',
  'You manage leave and cover': 'आप छुट्टी और स्थानापन्न देखते हैं',
  'You manage exam planning': 'आप परीक्षा योजना देखते हैं',
  'You manage people': 'आप लोगों को देखते हैं',
  // phone app tabs
  'Today': 'आज',
  'Progress': 'प्रगति',
  'Inbox': 'सूचनाएँ',
  'Papers': 'प्रश्नपत्र',
  'More': 'और',
  'Children': 'बच्चे',
  // common actions and headings
  'Submit': 'जमा करें',
  'Send again': 'फिर से भेजें',
  'Save': 'सहेजें',
  'Cancel': 'रद्द करें',
  'Practise': 'अभ्यास करें',
  'Practise again': 'फिर अभ्यास करें',
  'Check my answers': 'मेरे उत्तर जाँचें',
  'Revise next': 'आगे दोहराएँ',
  'Week by week': 'सप्ताह दर सप्ताह',
  'Written work': 'लिखित कार्य',
  'Take photo': 'फ़ोटो लें',
  'Choose photo': 'फ़ोटो चुनें',
  'Apply for leave': 'छुट्टी के लिए आवेदन',
  'My leave': 'मेरी छुट्टी',
  "Today's lessons": 'आज के पाठ',
  'Taught': 'पढ़ाया',
  'Not taught': 'नहीं पढ़ाया',
  'Cover asked of you': 'आपसे माँगा गया स्थानापन्न',
  'Accept': 'स्वीकार करें',
  'Decline': 'मना करें',
  "I'm here": 'मैं उपस्थित हूँ',
  'Set homework': 'गृहकार्य दें',
  'Mark all read': 'सब पढ़ा हुआ करें',
  'Nothing yet': 'अभी कुछ नहीं',
  'No homework': 'कोई गृहकार्य नहीं',
  'No marked work yet': 'अभी कोई जाँचा हुआ कार्य नहीं',
  'Consent given': 'सहमति दी गई',
  'Consent needed': 'सहमति चाहिए',
  'Week': 'सप्ताह',
  'Students who need help': 'जिन विद्यार्थियों को मदद चाहिए',
  'By chapter': 'अध्याय के अनुसार',
};
