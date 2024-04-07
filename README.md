# websockets_proxy

This module will enable you to use [websockets](https://github.com/python-websockets/websockets) package with proxies.

Proxy heavy-lifting is done by [python-socks](https://github.com/romis2012/python-socks) package.

# Usage

To install, use:

```
pip install websockets_proxy
```

All you need is create a proxy object and pass it into `proxy_connect` constructor:

```python
from websockets_proxy import Proxy, proxy_connect


proxy = Proxy.from_url("...")
async with proxy_connect("wss://example.com", proxy=proxy) as ws:
    ...
```

`proxy_connect` constructor accepts the same arguments as regular `connect` constructor, 
with the addition of `proxy` and `proxy_conn_timeout`, which are self-explanatory.

> **With this patch you cannot use `sock` keyword argument, because it is used to connect to a proxy server.**

> **You must create your `Proxy` objects within a running event loop** (inside an `async` function). 
> This is a [python-socks](https://github.com/romis2012/python-socks) limitation. 
> If you define your `Proxy` objects outside of running event loop, you'll get this kind of error: `RuntimeError: Task <Task pending name=...> attached to a different loop`.

# WebSocket proxy checker

## Server
Here is a simple `aiohttp` server, which allows you to check, if your proxy connections work as expected:

```python
import asyncio

from aiohttp import web, WSMsgType, WSMessage


HOST = '0.0.0.0'
PORT = 9999

app = web.Application()


async def websocket_handler(request: web.Request) -> web.StreamResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await ws.send_str(str(request.remote))
    await ws.close()
    print('accepted connection from', request.remote)
    return ws


app.add_routes([
    web.get('/', websocket_handler)
])


async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=HOST, port=PORT)
    await site.start()
    print('server is running')
    await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
```


## Client
An example of a client-side proxy checker script:

```python
import asyncio

from websockets_proxy import Proxy, proxy_connect
from websockets import connect


# this script is written with the above checker server in mind
CHECKER_URL = 'ws://address:port'


async def main():
    async with connect(CHECKER_URL) as ws:
        async for msg in ws:
            ip_no_proxy = msg
            print("Your IP:", ip_no_proxy)
    print('.')
    # be sure to create your "Proxy" objects inside an async function
    proxy = Proxy.from_url("http://login:password@address:port")
    async with proxy_connect(CHECKER_URL, proxy=proxy) as ws:
        async for msg in ws:
            ip_with_proxy = msg
            print("(async with) Proxy IP", ip_with_proxy)
    print('.')

    ws = await proxy_connect(CHECKER_URL, proxy=proxy)
    async for msg in ws:
        ip_with_proxy = msg
        print("(await) Proxy IP", ip_with_proxy)
    await ws.close()
    print('.')


if __name__ == "__main__":
    asyncio.run(main())

```
