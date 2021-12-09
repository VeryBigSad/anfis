from typing import Dict

import telegram
from telegram import Update

from tgbot.models import User

ALL_TG_FILE_TYPES = ["document", "video_note", "voice", "sticker", "audio", "video", "animation", "photo"]


def _get_file_id(m: Dict) -> str:
    """ extract file_id from message (and file type?) """

    for doc_type in ALL_TG_FILE_TYPES:
        if doc_type in m and doc_type != "photo":
            return m[doc_type]["file_id"]

    if "photo" in m:
        best_photo = m["photo"][-1]
        return best_photo["file_id"]


def show_file_id(update: Update, context) -> None:
    """ Returns file_id of the attached file/media """
    u = User.get_user(update, context)

    if u.is_admin:
        update_json = update.to_dict()
        file_id = _get_file_id(update_json["message"])
        message_id = update_json["message"]["message_id"]
        update.message.reply_text(
            text=f"`{file_id}`",
            parse_mode=telegram.ParseMode.HTML,
            reply_to_message_id=message_id
        )
