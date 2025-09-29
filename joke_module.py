__version__ = (1, 0, 0)

#      ________   _______  ________ _______      __       _______       __      
#     |"      "\ /"     "|/"       /"     "|    /""\     /"      \     /""\     
#     (.  ___  :(: ______(:   \___(: ______)   /    \   |:        |   /    \    
#     |: \   ) ||\/    |  \___  \  \/    |    /' /\  \  |_____/   )  /' /\  \   
#     (| (___\ ||// ___)_  __/  \\ // ___)_  //  __'  \  //      /  //  __'  \  
#     |:       :(:      "|/" \   :(:      "|/   /  \\  \|:  __   \ /   /  \\  \ 
#     (________/ \_______(_______/ \_______(___/    \___|__|  \___(___/    \___)
#                © Copyright 2025
#            ✈ https://t.me/desearamodules

# scope: hikka_only
# scope: hikka_min 1.3.3
# meta developer: @desearamodules

import aiohttp
from telethon import Button
from .. import loader, utils

@loader.tds
class JokeMod(loader.Module):

    strings = {
        "name": "JokeAPI",
        "_cls_doc": "Отправляет переведенные шутки с JokeAPI",
        "_cmd_doc_joke": "Отправляет случайную переведенную шутку с JokeAPI",
        "fetching": "🔄 Загружаю шутку...",
        "single_joke": "😂 <b>Шутка дня:</b>\n\n<i>{}</i>",
        "twopart_joke": "😂 <b>Шутка дня:</b>\n\n<b>❓ Вопрос:</b> <i>{}</i>\n<b>💡 Ответ:</b> <i>{}</i>",
        "api_error": "🚫 Ошибка API: Не удалось получить шутку. Попробуйте позже.",
        "no_joke": "🚫 Ошибка: Шутка с указанными параметрами не найдена.",
        "joke_description": "🎭 <b>JokeAPI Help</b>\n\n📝 <b>Использование:</b>\n• <code>.joke</code> - случайная шутка\n• <code>.joke [категория]</code> - шутка из категории\n\n🎭 <b>Доступные категории:</b>\n• Programming, Miscellaneous, Pun, Spooky, Christmas",
        "cfg_categories": "Категории по умолчанию, разделенные запятой",
        "cfg_blacklist": "Исключаемые категории, разделенные запятой",
        "translation_error": "⚠️ Не удалось перевести шутку, показываю оригинал"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "categories",
                "Programming,Miscellaneous,Pun,Spooky,Christmas",
                lambda: self.strings("cfg_categories"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "blacklist",
                "nsfw,religious,political,racist,sexist,explicit",
                lambda: self.strings("cfg_blacklist"),
                validator=loader.validators.String(),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self._db = db
        self.session = aiohttp.ClientSession()

    async def on_unload(self):
        await self.session.close()

    async def _format_joke(self, joke_data):
        if not joke_data:
            return None
            
        if joke_data["type"] == "single":
            joke_text = joke_data.get("joke", "")
            if not joke_text:
                return None
                
            translated = await self._translate_text(joke_text)
            if translated and translated.strip():
                text = self.strings("single_joke").format(translated)
            else:
                text = f"{self.strings('translation_error')}\n\n{self.strings('single_joke').format(joke_text)}"
                
        else:  # twopart joke
            setup_text = joke_data.get("setup", "")
            delivery_text = joke_data.get("delivery", "")
            if not setup_text or not delivery_text:
                return None
                
            translated_setup = await self._translate_text(setup_text)
            translated_delivery = await self._translate_text(delivery_text)
            
            if translated_setup and translated_delivery and translated_setup.strip() and translated_delivery.strip():
                text = self.strings("twopart_joke").format(
                    translated_setup,
                    translated_delivery
                )
            else:
                text = f"{self.strings('translation_error')}\n\n{self.strings('twopart_joke').format(setup_text, delivery_text)}"
        
        return text if text and text.strip() else None

    async def _translate_text(self, text, target_lang="ru"):
        if not text or not text.strip():
            return None
            
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": f"en|{target_lang}"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("responseStatus") == 200:
                        translated = data["responseData"]["translatedText"]
                        return translated if translated and translated.strip() else None
            
            # Fallback to Google Translate
            url2 = "https://translate.googleapis.com/translate_a/single"
            params2 = {
                "client": "gtx",
                "sl": "en",
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            
            async with self.session.get(url2, params=params2) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0 and len(data[0]) > 0:
                        translated = data[0][0][0]
                        return translated if translated and translated.strip() else None
                        
        except Exception:
            pass
        
        return None

    async def _fetch_joke(self, categories):
        params = {
            "lang": "en",
            "blacklistFlags": self.config["blacklist"],
        }

        url = f"https://v2.jokeapi.dev/joke/{categories}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data.get("error"):
                    return None
                    
                return data
        except Exception as e:
            return None

    @loader.command(ru_doc="Отправляет случайную переведенную шутку с JokeAPI")
    async def joke(self, message):
        args = utils.get_args_raw(message)
        
        if args and args.lower() in ["help", "помощь", "категории", "categories"]:
            await message.delete()
            await message.respond(self.strings("joke_description"), parse_mode="HTML")
            return
            
        await message.edit(self.strings("fetching"))

        categories = args if args else self.config["categories"]
        
        try:
            joke_data = await self._fetch_joke(categories)
            
            if not joke_data:
                await message.edit(f"🚫 API Error: Нет данных от API для категории '{categories}'")
                return
            
            joke_text = await self._format_joke(joke_data)

            if not joke_text or not joke_text.strip():
                await message.edit(f"🚫 Format Error: Не удалось обработать шутку. Тип: {joke_data.get('type', 'unknown')}")
                return

            await message.delete()
            await message.respond(joke_text, parse_mode="HTML")

        except Exception as e:
            await message.edit(f"🚫 Ошибка: {str(e)}")
