AIO HTTP stream
===============

Run a process, and stream its STDOUT in chunked HTTP.

Usage
-----



```python

# Define an handler
async def run_cmd(request):
    cmd = request.app["cmd"]
    # make an asyncio.subprocess.Process with arguments coming from the request.
    # here, the command is an app setting. Beware of command injection, it hurts
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    # delegate the response streaming to the helper
    await read_it_for_me(request, proc)

app = App() # default tuning
# plug your handler with its route
app.add_routes([web.get("/", run_cmd)])
app["cmd"] = "tree ~/Downloads/"

# start aiohttp server
web.run_app(app)
```

You can curl your service
```
curl -v http://localhost:8080/ > /tmp/answer
```

In the `X-Session` header, there is an id (an uuid).

List all sessions

```
curl http://localhost:8080/session
```

You can kill a running session

```
curl -XPUT  http://localhost:8080/session/42dcb9ecaeed4202b24d3611724a2b0c/_kill
```

Or getting information about a finished session
```
curl http://localhost:8080/session/42dcb9ecaeed4202b24d3611724a2b0c

{"id": "42dcb9ecaeed4202b24d3611724a2b0c",
 "size": 7484738,
 "hash": "261c9b606f8f29fbcc0eb2660acba260cae3efff2702ce5022673a4945784d6d"
}
```

`size` is the size of the answer, the chunking add few overhead.

`hash` is the SHA256 of the answer. If you `curl | sha256sum`, you must get the same hash.


Licence
-------

3 terms BSD licence. ©2020 Mathieu Lecarme.
