from .models import EventParticipation

def simple_bot_reply(user_message, user):
    """Chatbot GoGreen đơn giản"""
    user_message = user_message.lower().strip()

    # 1️⃣ Lời chào
    if any(word in user_message for word in ["chào", "hi", "hello", "xin chào"]):
        return f"🌿 Xin chào {user.username}! Mình là trợ lý GoGreen. Bạn muốn xem điểm, xem sự kiện hay cần hướng dẫn chuẩn bị không?"

    # 2️⃣ Xem điểm
    elif "điểm" in user_message or "bao nhiêu điểm" in user_message:
        return f"💚 Hiện tại bạn đang có **{user.points} điểm xanh**. Cứ mỗi lần tham gia dọn rác, bạn sẽ được cộng thêm điểm nhé!"

    # 3️⃣ Sự kiện của tôi
    elif any(kw in user_message for kw in ["sự kiện", "tôi tham gia", "đăng ký"]):
        participations = EventParticipation.objects.filter(user=user).select_related('event')
        if not participations.exists():
            return "📅 Bạn chưa đăng ký sự kiện nào. Hãy vào mục *Hoạt động* để tham gia nhé!"
        reply = "🗓️ Sự kiện của bạn:\n"
        for p in participations:
            reply += f"• {p.event.title} ({p.event.datetime_start.strftime('%d/%m %H:%M')}) tại {p.event.address or 'Chưa rõ'}\n"
        return reply

    # 4️⃣ Chuẩn bị lần đầu
    elif any(kw in user_message for kw in ["chuẩn bị", "mang gì", "lần đầu", "dọn rác"]):
        return (
            "🧤 Nếu đây là lần đầu bạn tham gia dọn rác, hãy chuẩn bị:\n"
            "• Găng tay bảo hộ 🤝\n"
            "• Bao rác hoặc túi phân loại ♻️\n"
            "• Nước uống 💧 và nón 👒\n"
            "• Áo GoGreen 👕 và giày kín mũi 👟\n"
            "Cảm ơn bạn đã góp phần làm sạch môi trường 🌱"
        )

    # 5️⃣ Mặc định
    else:
        return (
            "🤖 Mình chưa hiểu rõ câu hỏi. Bạn có thể hỏi:\n"
            "• 'Tôi có bao nhiêu điểm?'\n"
            "• 'Tôi đã đăng ký sự kiện nào?'\n"
            "• 'Lần đầu đi cần chuẩn bị gì?'"
        )
