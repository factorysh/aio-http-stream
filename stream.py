import asyncio
import uuid
from io import BytesIO

from aiohttp import web


async def read_process(process, read_stdout, read_stderr):
        out = asyncio.ensure_future(read_stdout(process.stdout))
        err = asyncio.ensure_future(read_stderr(process.stderr))
        return await asyncio.gather(out, err, process.wait())


async def run(cmd, read_out, read_err):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    await read_process(proc, read_out, read_err)
    print(proc.returncode)


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

    await run(request.app['cmd'], stdout, stderr)


if __name__ == "__main__":
    app = web.Application()
    app['cmd'] = 'tree ~/Downloads/'
    app['sessions'] = dict()
    app.add_routes(routes)
    web.run_app(app)
