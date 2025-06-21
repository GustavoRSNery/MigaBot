import os
from dotenv import load_dotenv
import telebot
from migo_assessor_ia import MigoAssessorIA 

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Token do Telegram não encontrado! Verifique seu arquivo .env")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_sessions = {}

def get_user_session(chat_id: int) -> MigoAssessorIA:
    if chat_id not in user_sessions:
        print(f"💬 Iniciando nova sessão para o usuário {chat_id}...")
        try:
            user_sessions[chat_id] = MigoAssessorIA()
        except Exception as e:
            print(f"🚨 Falha ao criar instância de MigoAssessorIA para {chat_id}: {e}")
            return None
    return user_sessions[chat_id]

@bot.message_handler(commands=['start', 'ajuda'])
def send_welcome(message):
    chat_id = message.chat.id
    try:
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        assessor_migo = get_user_session(chat_id)
        
        bot.send_chat_action(chat_id, 'typing')
        primeira_resposta = assessor_migo.enviar_relato("Olá, pode se apresentar por favor?")
        bot.reply_to(message, primeira_resposta)
    except Exception as e:
        print(f"🚨 Erro no handler 'send_welcome': {e}")
        bot.reply_to(message, "Ocorreu um erro ao iniciar. Tente o comando /start novamente.")

@bot.message_handler(func=lambda message: message.text.lower() in [
    'adeus', 'tchau', 'até logo', 'bye', 'flw', 'sair', 'finalizar', 'encerrar'
])
def goodbye(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')
    assessor_migo = get_user_session(chat_id)
    
    if assessor_migo:
        bot.reply_to(message, "Entendido. Finalizando nossa conversa e registrando o relato de forma segura e anônima... 📝")

        # É AQUI QUE A MÁGICA ACONTECE:
        # Chamamos o método da própria classe para gerar o resumo
        resumo_json_str = assessor_migo.gerar_resumo_json()
        
        print(f"\n--- 📄 RESUMO DO RELATO (Chat ID: {chat_id}) ---")
        print(resumo_json_str)
        bot.reply_to(message, f"Resumo: \n {resumo_json_str}")
        print("------------------------------------------------\n")
        
        del user_sessions[chat_id]
        print(f"🗑️ Sessão do usuário {chat_id} encerrada e resumo gerado.")
    else:
        bot.reply_to(message, "Não tínhamos uma conversa ativa, mas estou à disposição se precisar. Digite /start para começar. 👋")

@bot.message_handler(func=lambda message: True)
def responder_ia(message):
    chat_id = message.chat.id
    pergunta = message.text
    bot.send_chat_action(chat_id, 'typing')
    assessor_migo = get_user_session(chat_id)
    
    if not assessor_migo:
        bot.reply_to(message, "Desculpe, tivemos um problema. Por favor, digite /start para começar uma nova conversa.")
        return

    resposta = assessor_migo.enviar_relato(pergunta)
    bot.reply_to(message, resposta)

print("✅ Bot Telegram está rodando e pronto para conversar! 🤖")
bot.infinity_polling()