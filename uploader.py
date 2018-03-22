import os
import uuid

from aiohttp import web

from utils import get_ext, id_validator
from models import get_model_by_name
from sqlalchemy import select, exists, literal_column

uploader_routes = web.RouteTableDef()


@uploader_routes.post('/files/{user_id}')
async def upload_file(request: web.Request) -> web.Response:
    user_id = id_validator(request.match_info['user_id'], 'User')

    if request.content_type != 'multipart/form-data' or request.content_length == 0:
        return web.json_response(data=[])

    user_table = get_model_by_name('user')
    file_table = get_model_by_name('file')
    user_exists = await request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user_id)]))

    if not user_exists:
        await request.app['pg'].fetchrow(user_table.insert().values(**{'user_id': user_id}))

    reader = await request.multipart()
    upload_folder = request.app['config']['UPLOAD_FOLDER']
    data = []
    while not reader.at_eof():
        image = await reader.next()

        if not image:
            break

        file_name, ext = get_ext(image.filename)
        generated_file_name = '{}.{}'.format(uuid.uuid4(), ext)
        full_path = os.path.abspath(os.path.join(upload_folder, generated_file_name))
        size = 0

        with open(full_path, 'wb') as f:
            while True:
                chunk = await image.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)

        body = {'user_id': user_id,
                'name': image.filename,
                'path': full_path,
                'size': size}

        file = await request.app['pg'].fetchrow(file_table.insert().values(**body).returning(literal_column('*')))
        file = dict(file)
        file['creation_date'] = str(file['creation_date'])
        data.append(dict(file))

    return web.json_response(data=data)
