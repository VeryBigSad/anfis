def admin_proxy_information_text(public_proxy_count, public_working_proxy_count):
    return f'Загружено публичных прокси: <b>{public_proxy_count}</b>\n' \
           f'Из них рабочих: <b>{public_working_proxy_count}</b>'


def user_private_proxy_information_text(user_proxies_count, MINUTES_TO_CHECK_PUBLIC_PROXY):
    return f"🤷‍♂️ На данный момент используются <b>ваши личные</b> прокси.\n" \
           f"<b>Количество прокси:</b> <code>{user_proxies_count}</code>\n" \
           f"❗️ Прочек происходит каждые <b>{MINUTES_TO_CHECK_PUBLIC_PROXY} минут</b>"


def user_public_proxy_information_text(public_proxy_count, MINUTES_TO_CHECK_PUBLIC_PROXY):
    return f"🤷‍♂️ На данный момент используются <b>публичные</b> прокси бота. " \
           f"<b>Количество прокси:</b> <code>{public_proxy_count}</code>\n" \
           f"❗️Прочек происходит каждые <b>{MINUTES_TO_CHECK_PUBLIC_PROXY} минут</b>"
