from typing import Optional, Union
from urllib.parse import urlparse

import websockets
from websockets.legacy.client import connect
from python_socks.async_.asyncio import Proxy


class ProxyConnect(connect):
    def __init__(  # noqa
            self,
            uri: str,
            *,
            proxy: Optional[Proxy],
            proxy_conn_timeout: Optional[Union[int, float]] = None,
            **kwargs
    ) -> None:
        self.uri = uri
        # This looks strange, but
        if "sock" in kwargs:
            raise ValueError("do not supply your own 'sock' kwarg - it's used internally by the wrapper")
        kwargs.pop("host", None)
        kwargs.pop("port", None)
        u = urlparse(uri)
        host = u.hostname
        if u.port:
            port = u.port
        else:
            if u.scheme == "ws":
                port = 80
            elif u.scheme == "wss":
                port = 443
                # setting for ssl (because we specify sock instead of host, port)
                kwargs["server_hostname"] = host
            else:
                raise ValueError("unknown scheme")
        self.__proxy: Proxy = proxy
        self.__proxy_conn_timeout: Optional[Union[int, float]] = proxy_conn_timeout
        self.__host: str = host
        self.__port: int = port
        # pass it to the super().__init__ call
        self.__kwargs = kwargs
        # We deliberately don't call the super().__init__ constructor method YET!

    def set_proxy(self, proxy: Proxy) -> None:
        self.__proxy = proxy

    async def __aenter__(self) -> websockets.WebSocketClientProtocol:
        # creating patched socket
        sock = await self.__proxy.connect(
            dest_host=self.__host,
            dest_port=self.__port,
            timeout=self.__proxy_conn_timeout
        )
        self.__kwargs["sock"] = sock
        # HACK: THE super().__init__ IS DELIBERATELY CALLED HERE!
        # It is because we need an already connected socket object inside the constructor,
        # but we've only just got it inside of this method
        super().__init__(self.uri, **self.__kwargs)  # noqa
        proto = await super().__aenter__()
        return proto


proxy_connect = ProxyConnect

__all__ = ["proxy_connect", "Proxy"]
