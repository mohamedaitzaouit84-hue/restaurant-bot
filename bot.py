import anthropic
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# ============================================================
# البوت جاهز 100% - انسخ والصق وشغّل مباشرة
# لا تحتاج Twilio - يعمل مباشرة في المتصفح للاختبار
# ============================================================

ANTHROPIC_API_KEY = "ضع-مفتاحك-هنا"  # فقط هذا السطر تعدله

RESTAURANT = {
    "name": "مطعم الأصيل",
    "menu": {
        "دجاج مشوي كامل": "85 درهم",
        "كباب لحم 6 قطع": "70 درهم",
        "تاجين لحم بالخضر": "65 درهم",
        "شيش طاووق": "60 درهم",
        "حمص بالطحينة": "25 درهم",
        "سلطة مشكلة": "20 درهم",
        "عصير برتقال طازج": "20 درهم",
        "شاي مغربي": "10 درهم",
        "كنافة": "35 درهم",
    },
    "info": """
- العنوان: شارع محمد الخامس، الدار البيضاء
- ساعات العمل: 12 ظهراً حتى 11 مساءً
- التوصيل: 30-45 دقيقة، الحد الأدنى 80 درهم
- عرض العائلة: دجاج كامل + 4 مقبلات + 4 مشروبات = 150 درهم
- طلب فوق 200 درهم = توصيل مجاني
"""
}

conversations = {}

def get_ai_response(user_id, message):
    menu_text = "\n".join([f"- {k}: {v}" for k, v in RESTAURANT["menu"].items()])
    
    system = f"""أنت مساعد ذكي لـ {RESTAURANT['name']}.
قائمة الطعام:
{menu_text}

معلومات المطعم:
{RESTAURANT['info']}

- رد دائماً بالعربية بأسلوب ودي
- ساعد العميل في الطلب خطوة بخطوة
- عند تأكيد الطلب اطلب الاسم والعنوان والهاتف
- استخدم الإيموجي باعتدال"""

    if user_id not in conversations:
        conversations[user_id] = []
    
    conversations[user_id].append({"role": "user", "content": message})
    
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]
    
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system,
            messages=conversations[user_id]
        )
        reply = response.content[0].text
        conversations[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"خطأ: {e}"


# ============================================================
# واجهة ويب بسيطة للاختبار من المتصفح
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
  .header-info h2 { font-size: 16px; color: #fff; }
  .header-info p { font-size: 12px; color: #25d366; }
  
  .chat { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: #111; }
  
  .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; word-wrap: break-word; }
  .bot { background: #1e3a2f; color: #e8f5e9; border-radius: 12px 12px 12px 2px; align-self: flex-start; }
  .user { background: #25d366; color: #000; border-radius: 12px 12px 2px 12px; align-self: flex-end; }
  
  .input-area { background: #1a1a1a; padding: 12px; display: flex; gap: 10px; border-top: 1px solid #333; }
  input { flex: 1; background: #2a2a2a; border: 1px solid #444; color: #fff; padding: 12px 15px; border-radius: 25px; font-size: 14px; outline: none; font-family: Arial; direction: rtl; }
  input:focus { border-color: #25d366; }
  button { background: #25d366; border: none; color: #000; width: 45px; height: 45px; border-radius: 50%; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
  button:active { background: #128c7e; }
  
  .typing { color: #25d366; font-size: 13px; padding: 5px 10px; }
  
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
</style>
</head>
<body>

<div class="header">
  <div class="avatar">🍽️</div>
  <div class="header-info">
    <h2>مطعم الأصيل</h2>
    <p>● متصل الآن</p>
  </div>
</div>

<div class="chat" id="chat">
  <div class="msg bot">مرحباً بك في مطعم الأصيل! 🍽️<br>أنا مساعدك الذكي، كيف يمكنني مساعدتك اليوم؟<br><br>يمكنني مساعدتك في:<br>📋 عرض القائمة<br>🛒 تقديم طلب<br>ℹ️ معلومات المطعم</div>
</div>

<div class="input-area">
  <button onclick="sendMessage()">➤</button>
  <input id="msg" placeholder="اكتب رسالتك..." onkeypress="if(event.key==='Enter')sendMessage()" autofocus>
</div>

<script>
let userId = 'user_' + Math.random().toString(36).substr(2,9);

async function sendMessage() {
  const input = document.getElementById('msg');
  const text = input.value.trim();
  if (!text) return;
  
  addMessage(text, 'user');
  input.value = '';
  
  const chat = document.getElementById('chat');
  const typing = document.createElement('div');
  typing.className = 'typing';
  typing.id = 'typing';
  typing.textContent = '... يكتب';
  chat.appendChild(typing);
  chat.scrollTop = chat.scrollHeight;
  
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'msg=' + encodeURIComponent(text) + '&uid=' + userId
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    addMessage(data.reply, 'bot');
  } catch(e) {
    document.getElementById('typing')?.remove();
    addMessage('حدث خطأ، تأكد من مفتاح API', 'bot');
  }
}

function addMessage(text, type) {
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg ' + type;
  div.innerHTML = text.replace(/\\n/g, '<br>');
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
</script>
</body>
</html>"""


class BotHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # إخفاء logs

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        params = parse_qs(body)
        
        msg = params.get('msg', [''])[0]
        uid = params.get('uid', ['default'])[0]
        
        reply = get_ai_response(uid, msg)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps({"reply": reply}, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))


if __name__ == "__main__":
    print("=" * 45)
    print("  بوت مطعم الأصيل يعمل!")
    print("=" * 45)
    print("  افتح المتصفح على:")
    print("  http://localhost:8080")
    print("=" * 45)
    
    server = HTTPServer(('0.0.0.0', 8080), BotHandler)
    server.serve_forever()
