#      ________   _______  ________ _______      __       _______       __      
#     |"      "\ /"     "|/"       /"     "|    /""\     /"      \     /""\     
#     (.  ___  :(: ______(:   \___(: ______)   /    \   |:        |   /    \    
#     |: \   ) ||\/    |  \___  \  \/    |    /' /\  \  |_____/   )  /' /\  \   
#     (| (___\ ||// ___)_  __/  \\ // ___)_  //  __'  \  //      /  //  __'  \  
#     |:       :(:      "|/" \   :(:      "|/   /  \\  \|:  __   \ /   /  \\  \ 
#     (________/ \_______(_______/ \_______(___/    \___|__|  \___(___/    \___)
#                © Copyright 2025
#            ✈ https://t.me/desearamodules
# Name: Lejal Key
# Description: Interaction with @lejal_bot for random memes
# Author: @deseara


__version__ = (1, 0, 0)

from .. import loader, utils
import asyncio
import logging

logger = logging.getLogger(__name__)

@loader.tds
class LejalKey(loader.Module):
    """Interaction with @lejal_bot for random memes"""

    strings = {
        "name": "LejalKey",
        "requesting": "<emoji document_id=5328274090262275771>⏳</emoji> <b>Запрашиваю мем у @lejal_bot...</b>",
        "error": "<emoji document_id=5328145443106873128>❌</emoji> <b>Ошибка при получении мема от @lejal_bot</b>",
        "timeout": "<emoji document_id=5328145443106873128>⏰</emoji> <b>Таймаут ожидания ответа от @lejal_bot</b>",
        "bot_not_found": "<emoji document_id=5328145443106873128>🤖</emoji> <b>Бот @lejal_bot не найден или недоступен</b>",
        "no_response": "<emoji document_id=5328145443106873128>📵</emoji> <b>@lejal_bot не ответил</b>",
        "success": "<emoji document_id=5328239124933515868>✅</emoji> <b>Мем получен от @lejal_bot:</b>",
    }

    strings_ru = {
        "requesting": "<emoji document_id=5328274090262275771>⏳</emoji> <b>Запрашиваю мем у @lejal_bot...</b>",
        "error": "<emoji document_id=5328145443106873128>❌</emoji> <b>Ошибка при получении мема от @lejal_bot</b>",
        "timeout": "<emoji document_id=5328145443106873128>⏰</emoji> <b>Таймаут ожидания ответа от @lejal_bot</b>",
        "bot_not_found": "<emoji document_id=5328145443106873128>🤖</emoji> <b>Бот @lejal_bot не найден или недоступен</b>",
        "no_response": "<emoji document_id=5328145443106873128>📵</emoji> <b>@lejal_bot не ответил</b>",
        "success": "<emoji document_id=5328239124933515868>✅</emoji> <b>Мем получен от @lejal_bot:</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "TIMEOUT",
                10,
                lambda: "Таймаут ожидания ответа от бота (секунды)",
            ),
            loader.ConfigValue(
                "BOT_USERNAME",
                "lejal_bot",
                lambda: "Username бота (без @)",
            ),
        )

    async def client_ready(self, client, db):
        self.db = db
        self._client = client
        
        first_run = self.db.get("LejalKey", "first_run", True)
        if first_run:
            await self._add_to_archive()
            self.db.set("LejalKey", "first_run", False)

    async def _get_meme_from_bot(self, message):
        """Получить мем от @lejal_bot"""
        try:
            bot_username = self.config["BOT_USERNAME"]
            bot = await self._client.get_entity(f"@{bot_username}")
            
            await self._client.send_message(bot, "лежал ключ")
            
            timeout = self.config["TIMEOUT"]
            
            async def wait_for_response():
                for _ in range(timeout * 2):
                    await asyncio.sleep(0.5)
                    
                    messages = await self._client.get_messages(bot, limit=1)
                    if messages and messages[0].date:
                        # create by zov coder
                        import datetime
                        now = datetime.datetime.now(datetime.timezone.utc)
                        msg_time = messages[0].date
                        if (now - msg_time).total_seconds() < timeout:
                            return messages[0]
                return None
            
            response = await wait_for_response()
            return response
            
        except Exception as e:
            logger.error(f"Error getting meme from bot: {e}")
            return None

    @loader.command()
    async def lejalcmd(self, message):
        """| Получить случайный мем от @lejal_bot"""
        
        await utils.answer(message, self.strings["requesting"])
        
        try:
            # create by zov coder
            bot_response = await self._get_meme_from_bot(message)
            
            if not bot_response:
                await utils.answer(message, self.strings["no_response"])
                return
            
            await self._update_stats()
            
            if bot_response.photo:
                try:
                    caption = f"<blockquote>Мем от @lejal_bot</blockquote>"
                    await message.respond(caption, file=bot_response.photo)
                    await message.delete()
                except Exception as e:
                    if "TOPIC_CLOSED" in str(e):
                        await utils.answer(message, f"<blockquote>Мем от @lejal_bot</blockquote>\n\n📷 <i>Фото получено, но не удалось отправить (топик закрыт)</i>")
                    else:
                        await utils.answer(message, f"<blockquote>Мем от @lejal_bot</blockquote>\n\n❌ <i>Ошибка отправки фото: {str(e)}</i>")
            elif bot_response.text:
                response_text = f"<blockquote>Мем от @lejal_bot</blockquote>\n\n{bot_response.text}"
                await utils.answer(message, response_text)
            elif bot_response.sticker:
                try:
                    await message.respond(f"<blockquote>Мем от @lejal_bot</blockquote>", file=bot_response.sticker)
                    await message.delete()
                except Exception as e:
                    if "TOPIC_CLOSED" in str(e):
                        await utils.answer(message, f"<blockquote>Мем от @lejal_bot</blockquote>\n\n🎭 <i>Стикер получен, но не удалось отправить (топик закрыт)</i>")
                    else:
                        await utils.answer(message, f"<blockquote>Мем от @lejal_bot</blockquote>\n\n❌ <i>Ошибка отправки стикера: {str(e)}</i>")
            else:
                await utils.answer(message, self.strings["no_response"])
                
        except Exception as e:
            logger.error(f"Error in lejalcmd: {e}")
            await utils.answer(message, self.strings["error"])

    @loader.command()
    async def memecmd(self, message):
        """| Получить случайный мем от @lejal_bot (алиас для .lejal)"""
        await self.lejalcmd(message)

    @loader.command()
    async def keycmd(self, message):
        """| Получить случайный мем про ключ от @lejal_bot"""
        
        await utils.answer(message, self.strings["requesting"])
        
        try:
            bot_response = await self._get_meme_from_bot(message)
            
            if not bot_response:
                await utils.answer(message, self.strings["no_response"])
                return
            
            await self._update_stats()
            
            key_emoji = "🗝️"
            
            if bot_response.photo:
                try:
                    caption = f"<blockquote>Лежал ключ</blockquote>"
                    await message.respond(caption, file=bot_response.photo)
                    await message.delete()
                except Exception as e:
                    if "TOPIC_CLOSED" in str(e):
                        await utils.answer(message, f"<blockquote>Лежал ключ</blockquote>\n\n📷 <i>Фото получено, но не удалось отправить (топик закрыт)</i>")
                    else:
                        await utils.answer(message, f"<blockquote>Лежал ключ</blockquote>\n\n❌ <i>Ошибка отправки фото: {str(e)}</i>")
            elif bot_response.text:
                # create by zov coder
                response_text = f"<blockquote>Лежал ключ</blockquote>\n\n{bot_response.text}"
                await utils.answer(message, response_text)
            elif bot_response.sticker:
                try:
                    await message.respond(f"<blockquote>Лежал ключ</blockquote>", file=bot_response.sticker)
                    await message.delete()
                except Exception as e:
                    if "TOPIC_CLOSED" in str(e):
                        await utils.answer(message, f"<blockquote>Лежал ключ</blockquote>\n\n🎭 <i>Стикер получен, но не удалось отправить (топик закрыт)</i>")
                    else:
                        await utils.answer(message, f"<blockquote>Лежал ключ</blockquote>\n\n❌ <i>Ошибка отправки стикера: {str(e)}</i>")
            else:
                await utils.answer(message, self.strings["no_response"])
                
        except Exception as e:
            logger.error(f"Error in keycmd: {e}")
            await utils.answer(message, self.strings["error"])

    @loader.command()
    async def lejalstatscmd(self, message):
        """| Показать статистику взаимодействия с @lejal_bot"""
        
        stats_count = self.db.get("LejalKey", "requests_count", 0)
        last_request = self.db.get("LejalKey", "last_request", "Никогда")
        
        stats_text = f"""<emoji document_id=5328239124933515868>📊</emoji> <b>Статистика @lejal_bot:</b>

<emoji document_id=5328274090262275771>🔢</emoji> <b>Запросов отправлено:</b> {stats_count}
<emoji document_id=5328274090262275771>🕐</emoji> <b>Последний запрос:</b> {last_request}
<emoji document_id=5328274090262275771>🤖</emoji> <b>Бот:</b> @{self.config["BOT_USERNAME"]}
<emoji document_id=5328274090262275771>⏱️</emoji> <b>Таймаут:</b> {self.config["TIMEOUT"]}с"""

        await utils.answer(message, stats_text)

    @loader.command()
    async def lejalresetcmd(self, message):
        """| Сбросить статистику модуля"""
        
        self.db.set("LejalKey", "requests_count", 0)
        self.db.set("LejalKey", "last_request", "Никогда")
        self.db.set("LejalKey", "first_run", True)
        
        await utils.answer(message, "<emoji document_id=5328239124933515868>🔄</emoji> <b>Статистика модуля сброшена!</b>")

    @loader.command()
    async def lejalarchivecmd(self, message):
        """| Добавить мем от @lejal_bot в архив"""
        
        await utils.answer(message, "<emoji document_id=5328274090262275771>📁</emoji> <b>Добавляю мем в архив...</b>")
        try:
            await self._add_to_archive()
            await self._update_stats()
            await utils.answer(message, "<emoji document_id=5328239124933515868>✅</emoji> <b>Мем добавлен в архив!</b>")
        except Exception as e:
            logger.error(f"Error in lejalarchivecmd: {e}")
            await utils.answer(message, "<emoji document_id=5328145443106873128>❌</emoji> <b>Ошибка при добавлении в архив</b>")

    async def _update_stats(self):
        """Обновить статистику использования"""
        current_count = self.db.get("LejalKey", "requests_count", 0)
        self.db.set("LejalKey", "requests_count", current_count + 1)
        
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.set("LejalKey", "last_request", now)

    async def _add_to_archive(self):
        """Добавить 'лежал ключ' в архив при первом запуске"""
        try:
            bot_username = self.config["BOT_USERNAME"]
            bot = await self._client.get_entity(f"@{bot_username}")
            
            await self._client.send_message(bot, "лежал ключ")
            
            import asyncio
            await asyncio.sleep(2)
            
            messages = await self._client.get_messages(bot, limit=1)
            if messages and messages[0]:
                # create by zov coder
                try:
                    await messages[0].forward_to("me")
                except Exception as forward_error:
                    if "TOPIC_CLOSED" in str(forward_error):
                        logger.warning("Cannot forward to archive: topic closed")
                    else:
                        logger.error(f"Error forwarding to archive: {forward_error}")
                
        except Exception as e:
            logger.error(f"Error adding to archive: {e}")
