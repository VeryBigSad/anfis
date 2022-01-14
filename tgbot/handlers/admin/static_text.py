from datetime import timedelta

from django.utils.timezone import now

from tgbot.models import User

secret_admin_commands = f"⚠️ Secret Moderator commands\n" \
                        f"/admin - show this message\n" \
                        f"/stats - bot stats\n" \
                        f"⚠️ Admin-only commands from now on! ⚠️\n" \
                        f"/add_mod <username> - add a moderator\n" \
                        f"/remove_mod <username> - remove a moderator\n" \
                        f"/export_users - get user list in a .csv file\n" \
                        f"/broadcast <message> - send a message to all of the bot's users"

users_amount_stat = "<b>Users</b>: {user_count}\n" \
                    "<b>24h active</b>: {active_24}"

MODERATOR_ADDED = 'Successfully added {mod_name} as a moderator!'
MODERATOR_REMOVED = 'Successfully removed {mod_name} as a moderator!'
CANT_FIND_USER_WITH_NAME_OR_ID = "Couldn't find user with a username or id {username_or_id}"

remove_mod_usage = 'Usage: /remove_mod <mod_name>'


def admin_command_text():
    # TODO: finish off
    return f"""🙍Информация о пользователях
❕За все время: {User.objects.count()}
❕За месяц: {User.objects.filter(updated_at__gte=now() - timedelta(hours=24 * 30)).count()}
❕За неделю: {User.objects.filter(updated_at__gte=now() - timedelta(hours=24 * 7)).count()}
❕За день: {User.objects.filter(updated_at__gte=now() - timedelta(hours=24)).count()}

Количество купленных подписок:
❕За  3 месяца: COUNT_ALL_SUBS
❕За месяц: COUNT_MONTHLY_SUBS
❕За неделю: COUNT_WEEKLY_SUBS
❕За день: COUNT_DAILY_SUBS

Заработано:
❕За все время: COUNT_ALL_STONKS
❕За месяц: COUNT_MONTHLY_STONKS
❕За неделю: COUNT_WEEKLY_STONKS
❕За день: COUNT_DAILY_STONKS"""
