import asyncio
from asyncio.subprocess import Process
import uuid
from io import BytesIO
import hashlib
from typing import Callable

from aiohttp import web

from session import Session


class ReadingProcess:
    """
    Process wrapper for reading it with callbacks.
    """

    def __init__(
        self,
        process: Process,
        read_stdout: Callable[[asyncio.StreamReader], None],
        read_stderr: Callable[[asyncio.StreamReader], None],
    ):
        self.process = process
        self.out = asyncio.ensure_future(read_stdout(process.stdout))
        self.err = asyncio.ensure_future(read_stderr(process.stderr))

    async def wait(self) -> int:
        "Wait for process ending."
        await asyncio.gather(self.out, self.err)  # , self.process.wait())
        return self.process.returncode


async def run(cmd: str, read_out, read_err) -> ReadingProcess:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    return ReadingProcess(proc, read_out, read_err)


routes = web.RouteTableDef()

READ_CHUNK = 1024 ** 2
HTTP_CHUNK = 1024 ** 2


@routes.get("/")
async def run_cmd(request):
    r = web.StreamResponse()
    session = uuid.uuid4()
    r.headers["X-Session"] = session.hex
    await r.prepare(request)
    r.enable_chunked_encoding()

    class size:
        value = 0

        def incr(self, value):
            self.value += value

    s = size()
    m = hashlib.sha256()

    async def stdout(pipe):
        buffer = BytesIO()
        while True:
            chunk = await pipe.read(READ_CHUNK)
            if chunk == b"":
                break
            buffer.write(chunk)
            s.incr(len(chunk))
            m.update(chunk)
            poz = buffer.tell()
            if poz >= HTTP_CHUNK:
                buffer.seek(0)
                await r.write(buffer.read(poz))
                buffer.seek(0)
        poz = buffer.tell()
        if poz > 0:
            buffer.seek(0)
            await r.write(buffer.read(poz))
        await r.write_eof()

    async def stderr(pipe):
        while True:
            line = await pipe.readline()
            if len(line) == 0:
                break
            print(line)

    p = await run(request.app["cmd"], stdout, stderr)
    await p.wait()
    request.app["sessions"][session.hex] = dict(
        process=p, size=s.value, hash=m.hexdigest()
    )


@routes.get("/session")
async def sessions(request):
    return web.json_response(request.app["sessions"].keys())


@routes.get("/session/{id}")
async def session(request):
    _id = request.match_info["id"]
    if _id not in request.app["sessions"]:
        return web.Response(status=404)
    session = request.app["sessions"][_id]
    return web.json_response(dict(id=_id, size=session["size"], hash=session["hash"]))


@routes.put("/session/{id}/_kill")
async def kill(request):
    _id = request.match_info["id"]
    if _id not in request.app["sessions"]:
        return web.Response(status=404)
    session = request.app["sessions"][_id]
    session.process.kill()
    del request.app["sessions"][_id]
    return web.Response(status=204)


async def on_startup(app):
    async def loop():
        while True:
            await asyncio.sleep(app["sessions"].max_age)
            print("Garbage collection :", app["sessions"].garbage_collector())
    return asyncio.ensure_future(loop())


if __name__ == "__main__":
    app = web.Application()
    app["cmd"] = "cat ~/Downloads/UC-CAP_video.mp4"
    app["sessions"] = Session(max_size=100, max_age=180)
    app.on_startup.append(on_startup)
    app.add_routes(routes)
    web.run_app(app)
