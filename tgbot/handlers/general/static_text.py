help_command = 'туду: сделать помощь'
contact_command = '🔧 Техническая поддержка бота @chovash'

contact_button_text = '🛠 Поддержка'
token_spammer_button_text = '📨 Проспамить токены'
token_checker_button_text = '🔍 Чекер токенов'
nitro_service_button_text = '🚀 Вбивер нитро'
proxy_service_button_text = '📝 Прокси'
buy_subscription_button_text = '💵 Купить подписку'
admin_command_button_text = '🤐 Админка'

cancel_command = '🚁 Возвращение в главное меню'
cancel_button_action = '❌ Отмена'
buy_subscription_text = 'Для покупки доступа необходимо совершить оплату через Donation Alerts, ' \
                        'в сообщении прикрепив ваш <i>Telegram ID</i> И ВСЁ.\n' \
                        'Чтобы получить доступ на определенный срок — необходимо задонатить определенную сумму:\n' \
                        '<b>Месяц — 500 ₽</b>\n' \
                        '<b>3 месяца — 1000 ₽</b>\n' \
                        '<b>Год — 3000 ₽</b>\n' \
                        '<b>ВАЖНО</b> если вы задонатите сумму на рубль меньше или больше — подарите деньги проекту!'


def subbed_start_command(tg_username, user_id):
    return f'Привет, {tg_username} 👋🏻\n' \
           f'Добро пожаловать в <b>Discord Anfis</b>, ваш Telegram ID: <b>{user_id}</b>.\n' \
           f'Удачного ворка!'


def unsubbed_start_command(tg_username, user_id):
    return f'Привет, {tg_username} 👋🏻\n' \
           f'Добро пожаловать в <b>Discord Anfis</b>, ваш Telegram ID: <b>{user_id}</b>.'
