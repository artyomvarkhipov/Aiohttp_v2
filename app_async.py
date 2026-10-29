import json
from aiohttp import web
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from db import Session, Ad, close_db, init_db


async def orm_context(app: web.Application):
    print("START")
    await init_db()
    yield
    await close_db()
    print("END")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response


app = web.Application()
app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


def get_error(
        err_cls: type[web.HTTPNotFound | web.HTTPConflict | web.HTTPBadRequest],
        err_msg: dict | list | str,
):
    err_msg_json = {
        "error": err_msg,
    }
    return err_cls(
        text=json.dumps(err_msg_json),
        content_type="application/json",
    )


# Класс для действий с конкретным объявлением по ID
class AdView(web.View):

    @property
    def ad_id(self) -> int:
        return int(self.request.match_info["ad_id"])

    @property
    def session(self) -> AsyncSession:
        return self.request.session

    async def get_ad(self) -> Ad:
        ad = await self.session.get(Ad, self.ad_id)
        if ad is None:
            raise get_error(web.HTTPNotFound, err_msg="объявление не найдено")
        return ad

    # GET - получение объявления
    async def get(self):
        ad = await self.get_ad()
        return web.json_response(ad.dict)

    # PATCH - редактирование объявления
    async def patch(self):
        json_data = await self.request.json()
        ad = await self.get_ad()

        if "title" in json_data:
            ad.title = json_data["title"]
        if "description" in json_data:
            ad.description = json_data["description"]
        if "owner" in json_data:
            ad.owner = json_data["owner"]

        self.session.add(ad)
        await self.session.commit()
        return web.json_response(ad.id_dict)

    # DELETE - удаление объявления
    async def delete(self):
        ad = await self.get_ad()
        await self.session.delete(ad)
        await self.session.commit()
        return web.json_response({"result": "объявление успешно удалено"})


# Класс для действий со всеми объявлениями
class AdsListView(web.View):

    @property
    def session(self) -> AsyncSession:
        return self.request.session

    # GET - получение списка всех объявлений
    async def get(self):
        result = await self.session.execute(select(Ad))
        ads_all = result.scalars().all()
        return web.json_response([ad.dict for ad in ads_all])

    # POST - создание объявления с валидацией обязательных полей
    async def post(self):
        json_data = await self.request.json()

        # ВАЛИДАЦИЯ ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ
        if not ("title" in json_data and "description" in json_data and "owner" in json_data):
            raise get_error(
                web.HTTPBadRequest, err_msg="title, description и owner обязательны для заполнения"
            )

        new_ad = Ad(
            title=json_data["title"],
            description=json_data["description"],
            owner=json_data["owner"]
        )

        self.session.add(new_ad)
        await self.session.commit()
        return web.json_response(new_ad.id_dict, status=201)


app.add_routes(
    [
        web.post("/ads", AdsListView),
        web.get("/ads", AdsListView),
        web.get(r"/ads/{ad_id:\d+}", AdView),
        web.patch(r"/ads/{ad_id:\d+}", AdView),
        web.delete(r"/ads/{ad_id:\d+}", AdView),
    ]
)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8090)
