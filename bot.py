import anthropic
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============================================================
# 🍽️ إعدادات المطعم - غيّر فقط هذا القسم لكل عميل
# ============================================================

ANTHROPIC_API_KEY = "ضع-مفتاحك-هنا"  # مفتاح Anthropic الخاص بك

RESTAURANT = {
    "name": "مطعم الأصيل",
    "whatsapp": "212600000000",      # رقم واتساب المطعم بدون + مثلاً 212612345678
    "callmebot_key": "ضع-المفتاح-هنا", # مفتاح CallMeBot (شرح أدناه)
    "menu": {
        "دجاج مشوي كامل": 85,
        "كباب لحم 6 قطع": 70,
        "تاجين لحم بالخضر": 65,
        "شيش طاووق": 60,
        "حمص بالطحينة": 25,
        "سلطة مشكلة": 20,
        "عصير برتقال طازج": 20,
        "شاي مغربي": 10,
        "كنافة": 35,
    },
    "info": """
- العنوان: شارع محمد الخامس، الدار البيضاء
- ساعات العمل: 12 ظهراً حتى 11 مساءً
- التوصيل: 30-45 دقيقة، الحد الأدنى 80 درهم
- طلب فوق 200 درهم = توصيل مجاني
- عرض العائلة: دجاج + 4 مقبلات + 4 مشروبات = 150 درهم
"""
}

# ============================================================
# 📲 إرسال الطلب على واتساب المطعم عبر CallMeBot (مجاني)
# ============================================================

def send_whatsapp_to_restaurant(order_text):
    """إرسال الطلب لواتساب المطعم تلقائياً"""
    try:
        phone = RESTAURANT["whatsapp"]
        key = RESTAURANT["callmebot_key"]
        msg = urllib.parse.quote(order_text)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={msg}&apikey={key}"
        urllib.request.urlopen(url, timeout=10)
        print(f"✅ تم إرسال الطلب على واتساب: {order_text}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إرسال واتساب: {e}")
        return False


# ============================================================
# 🧠 نظام الذكاء الاصطناعي
# ============================================================

def get_system_prompt():
    menu_text = "\n".join([f"- {k}: {v} درهم" for k, v in RESTAURANT["menu"].items()])
    menu_json = json.dumps(RESTAURANT["menu"], ensure_ascii=False)

    return f"""أنت مساعد ذكي لـ {RESTAURANT['name']}.

قائمة الطعام:
{menu_text}

معلومات المطعم:
{RESTAURANT['info']}

تعليمات مهمة جداً:
1. ساعد العميل في اختيار طلبه من القائمة
2. عندما يؤكد العميل طلبه، اطلب منه: الاسم الكامل، العنوان، رقم الهاتف
3. بعد الحصول على هذه المعلومات الثلاث، احسب المجموع وأرسل رسالة تأكيد
4. في نهاية رسالة التأكيد أضف هذا السطر بالضبط:
   ORDER_CONFIRMED:اسم العميل|عنوانه|هاتفه|قائمة الطلبات والأسعار|المجموع
   مثال: ORDER_CONFIRMED:أحمد|شارع الحسن|0612345678|دجاج مشوي:85,شاي:10|95

5. رد دائماً بالعربية بأسلوب ودي
6. إذا طلب شيئاً غير موجود في القائمة اعتذر بلطف واقترح بديلاً
7. استخدم الإيموجي باعتدال"""


conversations = {}

def chat_with_ai(user_id, message):
    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": message})

    if len(conversations[user_id]) > 30:
        conversations[user_id] = conversations[user_id][-30:]

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=get_system_prompt(),
            messages=conversations[user_id]
        )
        reply = response.content[0].text
        conversations[user_id].append({"role": "assistant", "content": reply})

        # التحقق إذا كان الطلب مؤكداً وإرساله للمطعم
        if "ORDER_CONFIRMED:" in reply:
            order_data = reply.split("ORDER_CONFIRMED:")[1].strip().split("\n")[0]
            parts = order_data.split("|")
            if len(parts) >= 5:
                name, address, phone, items, total = parts[0], parts[1], parts[2], parts[3], parts[4]
                whatsapp_msg = f"""🍽️ طلب جديد - {RESTAURANT['name']}
━━━━━━━━━━━━━━━
👤 الاسم: {name}
📍 العنوان: {address}
📞 الهاتف: {phone}
━━━━━━━━━━━━━━━
🛒 الطلب:
{items.replace(',', chr(10))}
━━━━━━━━━━━━━━━
💰 المجموع: {total} درهم
━━━━━━━━━━━━━━━
⏰ وقت الطلب: الآن"""
                send_whatsapp_to_restaurant(whatsapp_msg)

            # إخفاء السطر التقني من رد العميل
            reply = reply.split("ORDER_CONFIRMED:")[0].strip()

        return reply

    except Exception as e:
        return f"عذراً حدث خطأ: {e}"


# ============================================================
# 🌐 واجهة الشات
# ============================================================

HTML_PAGE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>بوت مطعم الأصيل</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Arial; background: #0a0a0a; color: #fff; height: 100vh; display: flex; flex-direction: column; }
  .header { background: #1a1a2e; padding: 15px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #25d366; }
  .avatar { width: 45px; height: 45px; background: #25d366; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; }
  .header-info h2 { font-size: 16px; }
  .header-info p { font-size: 12px; color: #25d366; }
  .chat { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: #111; }
  .msg { max-width: 82%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-wrap: break-word; white-space: pre-wrap; }
  .bot { background: #1e3a2f; color: #e8f5e9; border-radius: 12px 12px 12px 2px; align-self: flex-start; }
  .user { background: #25d366; color: #000; border-radius: 12px 12px 2px 12px; align-self: flex-end; }
  .order-sent { background: #1a3a5c; color: #90caf9; border-radius: 8px; align-self: center; font-size: 13px; padding: 8px 16px; text-align: center; }
  .input-area { background: #1a1a1a; padding: 12px; display: flex; gap: 10px; border-top: 1px solid #333; }
  input { flex: 1; background: #2a2a2a; border: 1px solid #444; color: #fff; padding: 12px 15px; border-radius: 25px; font-size: 14px; outline: none; font-family: Arial; direction: rtl; }
  input:focus { border-color: #25d366; }
  button { background: #25d366; border: none; color: #000; width: 45px; height: 45px; border-radius: 50%; font-size: 20px; cursor: pointer; }
  .typing { color: #25d366; font-size: 13px; padding: 5px 15px; }
</style>
</head>
<body>
<div class="header">
  <div class="avatar">🍽️</div>
  <div class="header-info">
    <h2>مطعم الأصيل</h2>
    <p>● متصل الآن - 24/7</p>
  </div>
</div>
<div class="chat" id="chat">
  <div class="msg bot">مرحباً بك في مطعم الأصيل! 🍽️
أنا مساعدك الذكي، كيف يمكنني مساعدتك؟

يمكنني مساعدتك في:
📋 عرض القائمة
🛒 تقديم طلب
ℹ️ معلومات المطعم</div>
</div>
<div class="input-area">
  <button onclick="sendMessage()">➤</button>
  <input id="msg" placeholder="اكتب رسالتك..." onkeypress="if(event.key==='Enter')sendMessage()">
</div>
<script>
let uid = 'u_' + Math.random().toString(36).substr(2,9);

async function sendMessage() {
  const input = document.getElementById('msg');
  const text = input.value.trim();
  if (!text) return;
  addMsg(text, 'user');
  input.value = '';

  const chat = document.getElementById('chat');
  const t = document.createElement('div');
  t.className = 'typing'; t.id = 'typing'; t.textContent = '... يكتب';
  chat.appendChild(t); chat.scrollTop = chat.scrollHeight;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'msg=' + encodeURIComponent(text) + '&uid=' + uid
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    addMsg(data.reply, 'bot');
    if (data.order_sent) {
      addMsg('📲 تم إرسال طلبك للمطعم على واتساب!', 'order-sent');
    }
  } catch(e) {
    document.getElementById('typing')?.remove();
    addMsg('حدث خطأ، حاول مجدداً', 'bot');
  }
}

function addMsg(text, type) {
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg ' + type;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
</script>
</body>
</html>"""


class BotHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        params = urllib.parse.parse_qs(body)

        msg = params.get('msg', [''])[0]
        uid = params.get('uid', ['default'])[0]

        reply = chat_with_ai(uid, msg)
        order_sent = "📲" in reply or "تم إرسال" in reply

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps({"reply": reply, "order_sent": order_sent}, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))


if __name__ == "__main__":
    print("=" * 45)
    print(f"  {RESTAURANT['name']} - بوت الطلبات")
    print("=" * 45)
    print("  افتح المتصفح: http://localhost:8080")
    print("=" * 45)
    server = HTTPServer(('0.0.0.0', 8080), BotHandler)
    server.serve_forever()
