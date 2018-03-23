import os
import uuid
import json

from aiohttp import web

from utils import get_ext, id_validator, row_to_dict, many_row_to_dict
from models import get_model_by_name
from sqlalchemy import select, exists, literal_column, and_

uploader_routes = web.RouteTableDef()


@uploader_routes.view('/{user_id}/files')
class UserFile(web.View):
    
    async def post(self):
        user_id = id_validator(self.request.match_info['user_id'], 'User')

        if self.request.content_type != 'multipart/form-data' or self.request.content_length == 0:
            return web.json_response(data=[])

        user_table = get_model_by_name('user')
        file_table = get_model_by_name('file')
        user_exists = await self.request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user_id)]))

        if not user_exists:
            await self.request.app['pg'].fetchrow(user_table.insert().values(**{'user_id': user_id}))

        reader = await self.request.multipart()
        upload_folder = self.request.app['config']['UPLOAD_FOLDER']
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

            file = await self.request.app['pg'].fetchrow(file_table.insert().values(**body).returning(literal_column('*')))
            file = row_to_dict(file, 'file')
            data.append(dict(file))

        return web.json_response(data=data)
    
    async def get(self):
        user_id = id_validator(self.request.match_info['user_id'], 'User')

        user_table = get_model_by_name('user')
        user_exists = await self.request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user_id)]))

        if not user_exists:
            raise web.HTTPNotFound(
                body=json.dumps({'error': f'User with id={user_id} not found'}),
                content_type='application/json')

        file_table = get_model_by_name('file')
        files = await self.request.app['pg'].fetch(file_table.select().where(file_table.c.user_id == user_id))
        files = many_row_to_dict(files, 'file')

        return web.json_response(data=files)


@uploader_routes.get('/{user_id}/files/{file_id}')
async def get_file(request: web.Request):
    user_id = id_validator(request.match_info['user_id'], 'User')
    file_id = id_validator(request.match_info['file_id'], 'File')

    user_table = get_model_by_name('user')
    user_exists = await request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user_id)]))

    if not user_exists:
        raise web.HTTPNotFound(
            body=json.dumps({'error': 'User not found'}),
            content_type='application/json')

    file_table = get_model_by_name('file')
    file_exists = await request.app['pg'].fetchval(select([exists().where(
        and_(file_table.c.id == file_id, file_table.c.user_id == user_id))]))

    if not file_exists:
        raise web.HTTPNotFound(
            body=json.dumps({'error': 'File not found'}),
            content_type='application/json')

    file = await request.app['pg'].fetchrow(file_table.select().where(file_table.c.id == file_id))
    file = row_to_dict(file, 'file')

    return web.FileResponse(path=file['path'], status=200)
