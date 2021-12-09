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
