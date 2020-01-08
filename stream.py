import asyncio

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

@routes.get('/')
async def run_cmd(request):
    r = web.StreamResponse()
    await r.prepare(request)
    r.enable_chunked_encoding()
    async def stdout(pipe):
        while True:
            chunk = await pipe.read(1024 ** 2)
            if chunk == b"":
                break
            await r.write(chunk)
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
    app.add_routes(routes)
    web.run_app(app)
