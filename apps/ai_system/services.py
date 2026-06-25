"""
Groq AI xizmatlari - Smart Search, Auto SEO, Recommendation va boshqalar.
"""
import json
import requests
from django.conf import settings


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(messages, max_tokens=1024, temperature=0.7):
    """Groq API ga so'rov yuborish."""
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return None


def ai_smart_search(query, products_context=""):
    """
    AI Smart Search - foydalanuvchi oddiy tilida yozadi,
    AI kerakli mahsulotlarni topishga yordam beradi.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Sen Digsell.uz marketplace platformasi uchun professional AI qidiruv ekspertisan. "
                "Foydalanuvchi so'rovini tahlil qil va unga mos keladigan kalit so'zlarni va kategoriyalarni aniqla. "
                "Xato qilishga haqqing yo'q. Faqat haqiqiy ehtiyojga qarab tavsiya ber. "
                "Javobni FAQAT quyidagi JSON formatda ber:\n"
                '{"keywords": ["kalit", "so\'zlar"], "category_hint": "kategoriya nomi", "price_range": "narx oralig\'i", "suggestion": "Foydalanuvchi uchun qisqa va professional tavsiya"}\n'
                "O'zbek tilida javob ber. JSONdan boshqa hech qanday matn qo'shma."
            )
        },
        {
            "role": "user",
            "content": f"Foydalanuvchi qidirmoqda: \"{query}\"\n\nMavjud kontekst: {products_context}"
        }
    ]
    result = _call_groq(messages, max_tokens=400, temperature=0.1) # Temperature pastroq qilindi (aniqlik uchun)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {"keywords": [query], "category_hint": None, "price_range": None, "suggestion": result}
    return {"keywords": [query], "category_hint": None, "price_range": None, "suggestion": None}


def ai_auto_seo(title, description="", product_type=""):
    """
    AI Auto Title & SEO - mahsulot uchun professional SEO kontenti yaratish.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Sen professional SEO va Copywriting ekspertisan. "
                "Marketplace mahsulotlari uchun yuqori konversiyali sarlavha va tavsiflar yaratasan. "
                "Sening vazifang - mahsulotni jozibali va qidiruv tizimlariga mos qilish. "
                "Javobni FAQAT quyidagi JSON formatda ber:\n"
                '{"seo_title": "Optimallashgan professional sarlavha", '
                '"seo_description": "150 belgigacha jozibali meta tavsif", '
                '"tags": ["tag1", "tag2", "tag3", "tag4", "tag5"], '
                '"preview_text": "Xaridorni o\'ziga tortadigan qisqa matn"}\n'
                "O'zbek tilida professional uslubda yoz. Faqat JSON qaytar."
            )
        },
        {
            "role": "user",
            "content": f"Mahsulot: {title}\nTavsif: {description}\nTur: {product_type}"
        }
    ]
    result = _call_groq(messages, max_tokens=600, temperature=0.4)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return None
    return None


def ai_product_recommendation(user_history, available_products):
    """
    AI Product Recommendation - Foydalanuvchi qiziqishlariga asoslangan shaxsiylashtirilgan tavsiyalar.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Sen Netflix yoki Amazon darajasidagi aqlli tavsiya tizimisan. "
                "Foydalanuvchi tarixini tahlil qilib, unga eng mos mahsulotlarni tanlab ber. "
                "Tavsiyalar mantiqiy va foydali bo'lishi shart. "
                "Javobni FAQAT JSON formatda ber: "
                '[{"product_id": 1, "reason": "Nima uchun tavsiya qilingani haqida qisqa izoh"}]\n'
                "Faqat JSON qaytar."
            )
        },
        {
            "role": "user",
            "content": f"User tarixi: {user_history}\nMavjud mahsulotlar: {available_products}"
        }
    ]
    result = _call_groq(messages, max_tokens=500, temperature=0.3)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return []
    return []


def ai_chat_assistant(user_message, context=""):
    """
    AI Assistant - ChatGPT darajasidagi chuqur fikrlovchi platforma yordamchisi.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Sen Digsell.uz platformasining bosh intellektual yordamchisisan. "
                "Sening fikrlashing ChatGPT kabi chuqur, mantiqiy va kreativ bo'lishi shart. "
                "Faqat quruq javob bermasdan, foydalanuvchining niyatini tushunib, unga haqiqiy qiymat beradigan maslahatlar ber.\n\n"
                "PLATFORMA HAQIDA MA'LUMOT:\n"
                "- Nom: Digsell.uz (O'zbekistondagi raqamli mahsulotlar va freelance bozori)\n"
                "- Maqsad: O'zbek dasturchilari, dizaynerlari va kontent yaratuvchilari uchun o'z raqamli mahsulotlarini (skriptlar, botlar, dizaynlar) sotish va freelance loyihalarni topish uchun xavfsiz maydon yaratish.\n"
                "- Imkoniyatlar: Xavfsiz bitim (Escrow), AI qidiruv, AI SEO tahlil, Real-time chat, Seller reytingi.\n\n"
                "KO'RSATMALAR:\n"
                "1. Hech qachon 'tahlil o'tkazyapman' kabi umumiy gaplar bilan cheklanma. Darhol aniq va tushunarli javob ber.\n"
                "2. Agar foydalanuvchi sayt haqida so'rasa, unga platformaning foydasi va imkoniyatlarini hayotiy misollar bilan tushuntir.\n"
                "3. O'zbek tilida juda mukammal, xatosiz va samimiy gaplash.\n"
                "4. ChatGPT kabi har bir mavzuni chuqur yoritib ber, kerak bo'lsa qisqa punktlar bilan tushuntir.\n"
                "5. Foydalanuvchiga biznes-strategiyalar, sotuvlarni oshirish va raqamli biznes bo'yicha maslahatlar ber."
                f"\n\nQo'shimcha kontekst: {context}"
            )
        },
        {"role": "user", "content": user_message}
    ]
    # Temperature 0.7 - kreativlik va 'aqlli' fikrlash uchun optimal
    return _call_groq(messages, max_tokens=1500, temperature=0.7)


def ai_scam_detector(seller_data):
    """
    AI Scam Detector - shubhali faoliyatni aniqlash.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Sen marketplace uchun fraud/scam aniqlovchi AI tizimisan. "
                "Berilgan seller ma'lumotlarini tahlil qil va xavf darajasini aniqla. "
                "Javobni faqat JSON formatda ber:\n"
                '{"risk_level": "low/medium/high/critical", "reasons": ["sabab1"], "recommendation": "tavsiya"}\n'
                "Faqat JSON qaytar."
            )
        },
        {
            "role": "user",
            "content": f"Seller ma'lumotlari:\n{json.dumps(seller_data, ensure_ascii=False)}"
        }
    ]
    result = _call_groq(messages, max_tokens=400, temperature=0.2)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {"risk_level": "unknown", "reasons": [], "recommendation": result}
    return {"risk_level": "unknown", "reasons": [], "recommendation": "Tekshirib bo'lmadi"}
