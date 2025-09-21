__version__ = (1, 5, 8)

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

import asyncio
import json
import logging
import time
import typing
import urllib.parse
import urllib.request

try:
    from herokutl.tl.types import Message
except Exception:
    Message = typing.Any

try:
    from .. import loader, utils
except Exception:
    try:
        from heroku import loader, utils
    except Exception:
        import loader
        import utils

try:
    from ..inline.types import InlineCall 
except Exception:
    try:
        from heroku.inline.types import InlineCall  
    except Exception:
        InlineCall = typing.Any 


logger = logging.getLogger(__name__)


API_APPDETAILS = "https://store.steampowered.com/api/appdetails"
API_STORESEARCH = "https://store.steampowered.com/api/storesearch/"


async def _fetch_json(url: str, params: dict[str, typing.Any], timeout: int = 20) -> dict:
    def _do() -> dict:
        q = urllib.parse.urlencode(params)
        full = f"{url}?{q}"
        req = urllib.request.Request(
            full,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://store.steampowered.com/",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
        except Exception:
            return {}
        try:
            return json.loads(data.decode("utf-8"))
        except Exception:
            return {}

    return await asyncio.to_thread(_do)


def _price_from_overview(ov: dict | None) -> tuple[typing.Optional[int], typing.Optional[int], str]:
    if not isinstance(ov, dict):
        return None, None, ""
    return (
        ov.get("final"),
        ov.get("discount_percent"),
        ov.get("currency", ""),
    )


@loader.tds
class SteamWatch(loader.Module):
    strings = {
        "name": "SteamMonitor",
        "added": "<emoji document_id=5454419255430767770>📎</emoji>Добавлено: <b>{name}</b>{extra}",
        "removed": "<emoji document_id=5235927882466876283>🗑</emoji>Удалено: <b>{name}</b>",
        "not_tracked": "<emoji document_id=5454419255430767770>❔</emoji>Не найдено в отслеживании: <b>{query}</b>",
        "list_empty": "Пока ничего не отслеживается. Используй .steamadd <название|appid> [цена]",
        "list_item": "• <b>{name}</b> — {price} {cur} (-{disc}%)",
        "saved": "<emoji document_id=5454419255430767770>💾</emoji>Сохранено",
        "region_set": "<emoji document_id=5454419255430767770>🌍</emoji>Регион установлен: <code>{cc}</code>",
        "notify_here": "<emoji document_id=5454419255430767770>🔔</emoji>Уведомления будут приходить сюда: <code>{chat}</code>",
        "checking": "<emoji document_id=5454419255430767770>⏳</emoji>Проверяю цены...",
        "check_done": "<emoji document_id=5454419255430767770>✅</emoji>Проверка завершена",
        "price_drop": (
            "<emoji document_id=5454419255430767770>💥</emoji>Скидка в Steam\n"
            "<b>{name}</b>\n"
            "Цена: <b>{price}</b> {cur} (-{disc}%)\n"
            "Было: {old_price} {cur}\n"
            "{url}"
        ),
        "target_hit": (
            "<emoji document_id=5454419255430767770>🎯</emoji>Целевая цена достигнута\n"
            "<b>{name}</b> теперь {price} {cur} (-{disc}%)\n"
            "Цель: {target} {cur}\n"
            "{url}"
        ),
        "bad_args": "Использование: .steamadd <название|appid> [цена]",
        "search_empty": "Ничего не найдено",
        "search_item": "• <b>{name}</b>",
        "choose_game": "<emoji document_id=5454419255430767770>🔎</emoji>Выбери игру:",
        "target_too_high": (
            "<emoji document_id=5454419255430767770>⚠️</emoji>Целевая цена выше текущей.\n"
            "Текущая: <b>{price}</b> {cur}. Укажи цену не выше текущей."
        ),
        "cmd_steamadd": "Добавить игру: .steamadd <название|appid> [цена]",
        "cmd_steamrm": "Удалить игру: .steamrm <название|appid>",
        "cmd_steamlist": "Список отслеживаемых игр",
        "cmd_steamlistprice": "Список игр по цене (дешевле → дороже)",
        "cmd_steamsearch": "Поиск игр: .steamsearch <запрос>",
        "cmd_steamregion": "Регион Steam: .steamregion <cc> (ru/us и т.д.)",
        "cmd_steamnotifyhere": "Отправлять уведомления в этот чат",
        "cmd_steamcheck": "Проверить цены сейчас",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "region_cc",
                "us",
                "Двухбуквенный код региона Steam (например: ru, ua, us, eu)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "check_interval_min",
                60,
                "Интервал проверки в минутах",
                validator=loader.validators.Integer(minimum=5, maximum=1440),
            ),
            loader.ConfigValue(
                "discount_threshold",
                0,
                "Минимальный процент скидки для уведомлений",
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
            loader.ConfigValue(
                "notify_chat",
                0,
                "ID чата для уведомлений (по умолчанию — текущий при .steamnotifyhere)",
                validator=loader.validators.Integer(),
            ),
        )

        self._apps: dict[str, dict] = {}

    @property
    def _db_key(self) -> str:
        return f"{self.__class__.__name__}:apps"

    def _load(self) -> None:
        self._apps = self._db.get(self._db_key, "data", {}) or {}

    def _save(self) -> None:
        self._db.set(self._db_key, "data", self._apps)

    async def _get_app_details(self, appid: str) -> tuple[str, typing.Optional[int], typing.Optional[int], str]:
        params = {
            "appids": appid,
            "cc": self.config["region_cc"],
            "l": "english",
            "filters": "price_overview",
        }
        data = await _fetch_json(API_APPDETAILS, params)
        node = data.get(appid) if isinstance(data, dict) else None
        if not (isinstance(node, dict) and node.get("success")):
            return appid, None, None, ""

        d = node.get("data", {})
        name = d.get("name", f"App {appid}")
        price_overview = d.get("price_overview")
        price, disc, cur = _price_from_overview(price_overview)
        return name, price, disc, cur

    @loader.command()
    async def steamadd(self, message: Message):

        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("bad_args"))

        parts = args.split()
        appid = parts[0]
        target = None
        if len(parts) > 1:
            try:
                target = int(float(parts[1]) * 100)  
            except Exception:
                return await utils.answer(message, self.strings("bad_args"))

        
            search = await _fetch_json(
                API_STORESEARCH,
                {"term": appid, "cc": self.config["region_cc"], "l": "english"},
            )
            items = search.get("items") if isinstance(search, dict) else None
            if not items:
                return await utils.answer(message, self.strings("search_empty"))

            try:
                if self.inline.init_complete:
                    buttons = [
                        {
                            "text": str(it.get("name") or it.get("id")),
                            "callback": self._steamadd_select,
                            "args": (str(it.get("id")), target),
                        }
                        for it in items[:10]
                        if it.get("id")
                    ]
                    if await self.inline.form(
                        text=self.strings("choose_game"),
                        reply_markup=utils.chunks(buttons, 2)
                        + [[{"text": "✖️", "action": "close"}]],
                        message=message,
                    ):
                        return
            except Exception:
                pass

            # create by @deseara
            appid = str(items[0].get("id"))

        self._load()
        name, price, disc, cur = await self._get_app_details(appid)
        if target is not None and price is not None and target > price:
            return await utils.answer(
                message,
                self.strings("target_too_high").format(
                    price=f"{price/100:.2f}", cur=cur or ""
                ),
            )
        self._apps[appid] = {
            "name": name,
            "last_price": price,
            "last_disc": disc,
            "currency": cur,
            "target": target,
            "ts": int(time.time()),
        }
        self._save()

        extra = f" | цель: {target/100:.2f} {cur}" if target and cur else ""
        await utils.answer(message, self.strings("added").format(name=utils.escape_html(name or f"App {appid}"), extra=extra))

    async def _steamadd_select(self, call: InlineCall, appid: str, target: typing.Optional[int] = None):
        self._load()
        name, price, disc, cur = await self._get_app_details(appid)
        if target is not None and price is not None and target > price:
            return await call.edit(
                self.strings("target_too_high").format(
                    price=f"{price/100:.2f}", cur=cur or ""
                )
            )
        self._apps[appid] = {
            "name": name,
            "last_price": price,
            "last_disc": disc,
            "currency": cur,
            "target": target,
            "ts": int(time.time()),
        }
        self._save()
        extra = f" | цель: {target/100:.2f} {cur}" if target and cur else ""
        await call.edit(self.strings("added").format(name=utils.escape_html(name or f"App {appid}"), extra=extra))

    @loader.command()
    async def steamrm(self, message: Message):
        
        query = utils.get_args_raw(message)
        if not query:
            return await utils.answer(message, self.strings("bad_args"))

        self._load()
        appid = None
        if query.isdigit():
            if query in self._apps:
                appid = query
        else:
            for k, v in self._apps.items():
                if str(v.get("name", "")).lower() == query.lower():
                    appid = k
                    break
            if not appid:
                search = await _fetch_json(
                    API_STORESEARCH,
                    {"term": query, "cc": self.config["region_cc"], "l": "english"},
                )
                items = search.get("items") if isinstance(search, dict) else None
                if items:
                    appid = str(items[0].get("id"))

        if not appid or appid not in self._apps:
            return await utils.answer(message, self.strings("not_tracked").format(query=utils.escape_html(query)))

        name = self._apps.get(appid, {}).get("name") or f"App {appid}"
        del self._apps[appid]
        self._save()
        await utils.answer(message, self.strings("removed").format(name=utils.escape_html(name)))

    @loader.command()
    async def steamlist(self, message: Message):
        
        self._load()
        if not self._apps:
            return await utils.answer(message, self.strings("list_empty"))

        lines = []
        for appid, meta in self._apps.items():
            name = meta.get("name") or f"App {appid}"
            price = meta.get("last_price")
            disc = meta.get("last_disc") or 0
            cur = meta.get("currency") or ""
            if price is None:
                price_s = "n/a"
            else:
                price_s = f"{price/100:.2f}"
            lines.append(
                self.strings("list_item").format(
                    name=utils.escape_html(name),
                    price=price_s,
                    cur=cur,
                    disc=disc or 0,
                )
            )

        await utils.answer(message, "\n".join(lines))

    @loader.command()
    async def steamlistprice(self, message: Message):
        
        self._load()
        if not self._apps:
            return await utils.answer(message, self.strings("list_empty"))

        def price_key(item: tuple[str, dict]):
            _, meta = item
            p = meta.get("last_price")
            return (p is None, p or 10**12)  
        sorted_items = sorted(self._apps.items(), key=price_key)
        rows = []
        for appid, meta in sorted_items:
            name = meta.get("name") or f"App {appid}"
            price = meta.get("last_price")
            cur = meta.get("currency") or ""
            disc = meta.get("last_disc") or 0
            price_s = "n/a" if price is None else f"{price/100:.2f}"
            rows.append(
                self.strings("list_item").format(
                    name=utils.escape_html(name),
                    price=price_s,
                    cur=cur,
                    disc=disc,
                )
            )

        await utils.answer(message, "\n".join(rows))

    @loader.command()
    async def steamregion(self, message: Message):

        cc = utils.get_args_raw(message).lower()
        if not cc or len(cc) not in {2}:
            return await utils.answer(message, "Пример: .steamregion ru")
        self.config["region_cc"] = cc
        await utils.answer(message, self.strings("region_set").format(cc=cc))

    @loader.command()
    async def steamnotifyhere(self, message: Message):

        chat = getattr(message, "chat_id", None) or getattr(message, "peer_id", None)
        self.config["notify_chat"] = int(chat)
        await utils.answer(message, self.strings("notify_here").format(chat=chat))

    @loader.command()
    async def steamcheck(self, message: Message):

        await utils.answer(message, self.strings("checking"))
        await self._run_check(notify=True)
        await utils.answer(message, self.strings("check_done"))

    @loader.command()
    async def steamsearch(self, message: Message):

        q = utils.get_args_raw(message)
        if not q:
            return await utils.answer(message, "Пример: .steamsearch counter strike")
        data = await _fetch_json(
            API_STORESEARCH,
            {"term": q, "cc": self.config["region_cc"], "l": "english"},
        )
        items = data.get("items") if isinstance(data, dict) else None
        if not items:
            return await utils.answer(message, self.strings("search_empty"))
        text = []
        for it in items[:10]:
            name = it.get("name")
            appid = it.get("id")
            if not (name and appid):
                continue
            text.append(self.strings("search_item").format(name=utils.escape_html(name), appid=appid))
        await utils.answer(message, "\n".join(text) or self.strings("search_empty"))

    @loader.loop(autostart=True, interval=300)
    async def _loop(self):
        try:
            await self._run_check(notify=True)
        except Exception:
            logger.exception("SteamWatch loop failed")

    async def _run_check(self, notify: bool):
        self._load()
        if not self._apps:
            return

        cc = self.config["region_cc"]
        for appid, meta in list(self._apps.items()):
            try:
                name, price, disc, cur = await self._get_app_details(appid)
            except Exception:
                logger.exception("Failed to fetch app %s", appid)
                continue

            old_price = meta.get("last_price")
            old_disc = meta.get("last_disc") or 0
            target = meta.get("target")

            changed = price is not None and price != old_price
            hit_discount = (disc or 0) >= (self.config["discount_threshold"] or 0)
            hit_target = price is not None and target and price <= target

            meta.update(
                {
                    "name": name or meta.get("name"),
                    "last_price": price,
                    "last_disc": disc,
                    "currency": cur or meta.get("currency", ""),
                    "ts": int(time.time()),
                }
            )

            self._apps[appid] = meta

            if notify and price is not None and (changed or hit_target or hit_discount):
                chat = self.config.get("notify_chat")
                text = None
                url = f"https://store.steampowered.com/app/{appid}/"
                if hit_target and target is not None:
                    text = self.strings("target_hit").format(
                        name=utils.escape_html(name or f"App {appid}"),
                        price=f"{price/100:.2f}",
                        disc=disc or 0,
                        target=f"{target/100:.2f}",
                        cur=cur or "",
                        url=url,
                    )
                elif changed:
                    text = self.strings("price_drop").format(
                        name=utils.escape_html(name or f"App {appid}"),
                        price=f"{price/100:.2f}",
                        disc=disc or 0,
                        old_price=f"{(old_price or 0)/100:.2f}",
                        cur=cur or "",
                        url=url,
                    )

                if text:
                    try:
                        if chat:
                            await self._client.send_message(int(chat), text)
                        else:
                            await self._client.send_message("me", text)
                    except Exception:
                        logger.exception("Failed to send price notification")

        self._save()

    async def client_ready(self):
        try:
            minutes = int(self.config["check_interval_min"]) or 60
            self._loop.set_interval(minutes * 60)
        except Exception:
            pass
