import asyncio
import uuid
from io import BytesIO

from aiohttp import web

from session import Session


class ReadingProcess:
    def __init__(self, process, read_stdout, read_stderr):
        self.process = process
        self.out = asyncio.ensure_future(read_stdout(process.stdout))
        self.err = asyncio.ensure_future(read_stderr(process.stderr))

    async def wait(self):
        return await asyncio.gather(self.out, self.err, self.process.wait())


async def run(cmd: str, read_out, read_err) -> ReadingProcess:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    return ReadingProcess(proc, read_out, read_err)


routes = web.RouteTableDef()

READ_CHUNK = 1024 ** 2
HTTP_CHUNK = 1024 ** 2


@routes.get('/')
async def run_cmd(request):
    r = web.StreamResponse()
    session = uuid.uuid4()
    r.headers['X-Session'] = session.hex
    await r.prepare(request)
    r.enable_chunked_encoding()
    async def stdout(pipe):
        buffer = BytesIO()
        while True:
            chunk = await pipe.read(READ_CHUNK)
            if chunk == b"":
                break
            buffer.write(chunk)
            if buffer.tell() >= HTTP_CHUNK:
                buffer.seek(0)
                await r.write(buffer.read())
                buffer.seek(0)
        if buffer.tell() > 0:
            buffer.seek(0)
            await r.write(buffer.read())
        await r.write_eof()

    async def stderr(pipe):
        while True:
            line = await pipe.readline()
            if len(line) == 0:
                break
            print(line)

    p = await run(request.app['cmd'], stdout, stderr)
    request.app['sessions'][session.hex] = p
    await p.wait()


@routes.get('/session')
async def sessions(request):
    return web.json_response(request.app['sessions'].keys())

@routes.get('/session/{id}')
async def session(request):
    _id = request.match_info['id']
    if _id not in request.app['sessions']:
        return web.Response(status=404)
    session = request.app['sessions'][_id]
    return web.json_response(dict(id=_id, pid=session.process.pid))


if __name__ == "__main__":
    app = web.Application()
    app['cmd'] = 'tree ~/Downloads/'
    app['sessions'] = Session(max_size=100, max_age=180)
    app.add_routes(routes)
    web.run_app(app)
