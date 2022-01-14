import os

from telegram import ParseMode

from tgbot.handlers.utils import files


def send_document(user_id, file_data, filename222, caption):
    tard_filename = files.get_filepath_for_file('token_checker_result')

    from tgbot.dispatcher import bot
    with open(tard_filename, 'w') as f:
        f.write(file_data)
    with open(tard_filename, 'r') as f:
        bot.send_document(
            chat_id=user_id,
            filename=filename222,
            document=f,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
    os.remove(tard_filename)
