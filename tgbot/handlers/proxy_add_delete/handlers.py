import os

from django.utils import timezone
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler

from proxy_manager.models import Proxy
from tgbot.handlers.proxy_add_delete import static_text
from tgbot.handlers.proxy_add_delete.proxy_check_task import ping_proxies
from tgbot.handlers.utils import keyboard
from tgbot.handlers.utils.decorators import send_typing_action, handler_logging, admin_only_command, sub_only_command
from tgbot.handlers.utils import files
from tgbot.handlers.utils.files import get_line_list_from_file
from tgbot.models import User
from dtb.settings import MINUTES_TO_CHECK_PUBLIC_PROXY


@send_typing_action
@admin_only_command
@handler_logging()
def add_proxy_as_admin(update: Update, context: CallbackContext) -> None:
    """ adds public proxies """
    u = User.get_user(update, context)
    public_proxy_count = Proxy.objects.filter(owner=None).count()
    public_working_proxy_count = Proxy.objects.filter(owner=None, does_work=True).count()
    update.message.reply_text(
        text=static_text.admin_proxy_information_text(public_proxy_count, public_working_proxy_count),
        reply_markup=keyboard.admin_proxy_keyboard(), parse_mode=ParseMode.HTML
    )


@send_typing_action
@admin_only_command
@handler_logging()
def wait_new_admin_proxy(update: Update, context: CallbackContext) -> str:
    update.message.reply_text('Какие прокси вы будете загружать?',
                              reply_markup=keyboard.proxy_type(), parse_mode=ParseMode.HTML)
    return 'wait_txt_file'


@send_typing_action
@admin_only_command
@handler_logging()
def wait_txt_admin_proxy(update: Update, context: CallbackContext) -> str:
    context.user_data['admin_proxy_type'] = update.message.text
    update.message.reply_text('Скиньте .txt файл с прокси вида <b>user:password@ip:port</b>\n'
                              '<b>ВНИМАНИЕ!!!</b> если вы это сделаете, все старые прокси сотрутся. '
                              'Вы можете экспортировать их и добавить новые прокси в конец старого файла.',
                              reply_markup=keyboard.cancel_keyboard(), parse_mode=ParseMode.HTML)
    return 'process_new_admin_proxy'


@send_typing_action
@admin_only_command
@handler_logging()
def process_new_admin_proxy(update: Update, context: CallbackContext) -> str:
    u = User.get_user(update, context)

    update.message.reply_text("Удаляю все старые публичные прокси...", reply_markup=keyboard.remove_reply_keyboard())
    Proxy.objects.filter(is_public=True).delete()
    update.message.reply_text("Удалил!")

    file = update.message.document.get_file()
    filename = files.get_filepath_for_file('admin_proxy')
    file.download(filename)
    lines = [i for i in open(filename).read().split('\n') if i != '']
    os.remove(filename)

    file_type = context.user_data['admin_proxy_type']
    del context.user_data['admin_proxy_type']
    ping_proxies({i: file_type for i in lines}, 8, timezone.now(), u.user_id, None)
    return ConversationHandler.END



@send_typing_action
@admin_only_command
@handler_logging()
def export_admin_proxy(update: Update, context: CallbackContext) -> None:
    working_proxy = Proxy.objects.filter(is_public=True, does_work=True)
    if not working_proxy.exists():
        update.message.reply_text(
            "К сожалению, сейчас нет публичных рабочих прокси, так что там нечего выгружать :(",
            reply_markup=keyboard.admin_proxy_keyboard())
    else:
        for i in ['http', 'socks4', 'socks5']:
            this_scheme_proxy = working_proxy.filter(proxy_scheme=i)
            if not this_scheme_proxy.exists():
                continue
            filename1 = files.get_filepath_for_file('admin_woring_proxy_export')
            with open(filename1, 'w') as f:
                f.write('\n'.join([i.proxy_url for i in this_scheme_proxy]))
            with open(filename1, 'r') as f:
                update.message.reply_document(
                    document=f, filename=f'working_proxy_list_{i}.txt',
                    caption=f'<b>{this_scheme_proxy.count()} публичных рабочих прокси на протоколе {i}.</b>',
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard.admin_proxy_keyboard()
                )
            os.remove(filename1)
    # broken_proxy = Proxy.objects.filter(is_public=True, does_work=False)
    # if not broken_proxy.exists():
    #     update.message.reply_text("у тебя ни одного нерабочего прокси! ура!",
    #                               reply_markup=keyboard.admin_proxy_keyboard())
    # else:
    # for i in ['http', 'socks4', 'socks5']:
    #     this_scheme_proxy = working_proxy.filter(proxy_scheme=i)
    #     if not this_scheme_proxy.exists():
    #         continue
    #     filename = files.get_filepath_for_file('admin_broken_proxy_export')
    #     with open(filename, 'w') as f:
    #         f.write('\n'.join([i.proxy_url for i in working_proxy]))
    #     with open(filename, 'r') as f:
    #         update.message.reply_document(
    #             document=f, filename=f'broken_proxy_list_{i}.txt',
    #             caption=f'<b>{working_proxy.count()} публичных !НЕ!рабочих прокси на протоколе {i}.</b>',
    #             parse_mode=ParseMode.HTML,
    #             reply_markup=keyboard.admin_proxy_keyboard()
    #         )
    #     os.remove(filename)


@send_typing_action
@sub_only_command
@handler_logging()
def proxy_service(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    user_proxies = Proxy.objects.filter(owner=u, does_work=True)
    if user_proxies.exists():
        update.message.reply_text(
            static_text.user_private_proxy_information_text(user_proxies.count(), MINUTES_TO_CHECK_PUBLIC_PROXY),
            reply_markup=keyboard.proxy_buttons(u, True),
            parse_mode=ParseMode.HTML
        )
    else:
        public_proxy_count = Proxy.objects.filter(owner=None, does_work=True).count()
        update.message.reply_text(
            static_text.user_public_proxy_information_text(public_proxy_count, MINUTES_TO_CHECK_PUBLIC_PROXY),
            reply_markup=keyboard.proxy_buttons(u, False),
            parse_mode=ParseMode.HTML
        )


@send_typing_action
@sub_only_command
@handler_logging()
def add_proxy_1(update: Update, context: CallbackContext) -> str:
    u = User.get_user(update, context)
    update.message.reply_text(
        f"Чтобы добавить свои прокси, скиньте их в .txt файле в формате <code>user:pass@ip:port</code>.\n"
        f"<b>Если у вас уже установлены прокси, они будут удалены и заменены теми что вы скините сейчас.</b>",
        reply_markup=keyboard.cancel_keyboard(),
        parse_mode=ParseMode.HTML
    )
    return 'process_new_user_proxies'


@send_typing_action
@sub_only_command
@handler_logging()
def add_proxy_2(update: Update, context: CallbackContext) -> str:
    u = User.get_user(update, context)
    lines = get_line_list_from_file(update.message.document.get_file())
    ping_proxies({i: 'http' for i in lines}, 8, timezone.now(), u.user_id, u)
    return ConversationHandler.END


@send_typing_action
@sub_only_command
@handler_logging()
def delete_private_proxies(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    Proxy.objects.filter(owner=u).delete()
    update.message.reply_text('Ваши личные прокси были удалены!')
    proxy_service(update, context)

