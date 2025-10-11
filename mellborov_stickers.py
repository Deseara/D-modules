# ---------------------------------------------------------------------------------
#      ________   _______  ________ _______      __       _______       __      
#     |"      "\ /"     "|/"       /"     "|    /""\     /"      \     /""\     
#     (.  ___  :(: ______(:   \___(: ______)   /    \   |:        |   /    \    
#     (| (___\ ||// ___)_  __/  \\ // ___)_  //  __'  \  //      /  //  __'  \  
#     |:       :(:      "|/" \   :(:      "|/   /  \\  \|:  __   \ /   /  \\  \ 
#     (________/ \_______(_______/ \_______(___/    \___|__|  \___(___/    \___)
#                © Copyright 2025
#            ✈ https://t.me/desearamodules
# Name: Mellstroy am am am stikers
# Description: Random stickers from mellstroy da da net net da budet svet 
# Author: @deseara
# Commands: mell
# ---------------------------------------------------------------------------------

__version__ = (1, 0, 0)
from .. import loader, utils
import random
import logging

logger = logging.getLogger(__name__)

@loader.tds
class MellborovStickers(loader.Module):
    """Random stickers from mellstroy da da net net da budet svet"""
    strings = {
        "name": "MellborovStickers",
        "loading": "<emoji document_id=5431449001532594346>⏳</emoji> <b>Загружаю стикеры из mellborov...</b>",
        "error": "<emoji document_id=5431376038628171216>❌</emoji> <b>Ошибка при загрузке стикерпака</b>",
        "no_stickers": "<emoji document_id=5431736674147114227>📦</emoji> <b>Стикеры не найдены в паке mellborov</b>",
        "pack_not_found": "<emoji document_id=5431525149291454009>🔍</emoji> <b>Стикерпак mellborov не найден</b>",
        "sending_error": "<emoji document_id=5431811284089927962>📤</emoji> <b>Ошибка отправки стикера</b>",
    }

    strings_ru = {
        "loading": "<emoji document_id=5431449001532594346>⏳</emoji> <b>Загружаю стикеры из mellborov...</b>",
        "error": "<emoji document_id=5431376038628171216>❌</emoji> <b>Ошибка при загрузке стикерпака</b>",
        "no_stickers": "<emoji document_id=5431736674147114227>📦</emoji> <b>Стикеры не найдены в паке mellborov</b>",
        "pack_not_found": "<emoji document_id=5431525149291454009>🔍</emoji> <b>Стикерпак mellborov не найден</b>",
        "sending_error": "<emoji document_id=5431811284089927962>📤</emoji> <b>Ошибка отправки стикера</b>",
    }

    def __init__(self):
        self._stickers_cache = []
        self._cache_loaded = False
        self._sticker_pack = "mellborov"

    async def client_ready(self, client, db):
        self.db = db
        self._client = client

    async def _load_stickers(self):
        if self._cache_loaded and self._stickers_cache:
            return self._stickers_cache

        try:
            # create by zov coder
            from telethon.tl.functions.messages import GetStickerSetRequest
            from telethon.tl.types import InputStickerSetShortName
            
            stickerset = await self._client(GetStickerSetRequest(
                stickerset=InputStickerSetShortName(short_name=self._sticker_pack),
                hash=0
            ))
            
            if not stickerset or not stickerset.documents:
                logger.warning(f"No stickers found in pack: {self._sticker_pack}")
                return []
            
            self._stickers_cache = stickerset.documents
            self._cache_loaded = True
            
            logger.info(f"Loaded {len(self._stickers_cache)} stickers from {self._sticker_pack}")
            return self._stickers_cache
            
        except Exception as e:
            logger.error(f"Error loading stickers: {e}")
            return []

    async def _get_random_sticker(self):
        stickers = await self._load_stickers()
        
        if not stickers:
            return None
            
        return random.choice(stickers)

    @loader.command()
    async def mellcmd(self, message):
        """| Отправить случайный стикер бэм бэм бэм"""
        
        await utils.answer(message, self.strings["loading"])
        
        try:
            sticker = await self._get_random_sticker()
            
            if not sticker:
                await utils.answer(message, self.strings["no_stickers"])
                return
            
            try:
                await message.respond(file=sticker)
                await message.delete()
            except Exception as send_error:
                if "TOPIC_CLOSED" in str(send_error):
                    await utils.answer(message, f"<blockquote>Mellborov стикер</blockquote>\n\n<emoji document_id=5431376038628171216>🎭</emoji> <i>Стикер получен, но не удалось отправить (топик закрыт)</i>")
                else:
                    await utils.answer(message, f"{self.strings['sending_error']}\n<i>{str(send_error)}</i>")
                    
        except Exception as e:
            logger.error(f"Error in mellcmd: {e}")
            await utils.answer(message, self.strings["error"])

