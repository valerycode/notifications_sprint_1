import asyncio
import os
from datetime import datetime, timedelta, timezone

import jwt
import websockets

uri = "ws://websocket_sender:8888"
key = os.getenv("AUTH_JWT_KEY")


def generate_token():
    token = {"sub": "c3696fea-68d3-4de6-a854-0d101304d85d", "exp": datetime.now(tz=timezone.utc) + timedelta(hours=10)}
    return jwt.encode(token, key, algorithm="HS256")


async def main():
    async with websockets.connect(uri) as websocket:
        token = generate_token()
        await websocket.send(token)
        print(f"Connected to {uri}")

        async for message in websocket:
            print(f"Received message: {message}")


if __name__ == "__main__":
    asyncio.run(main())
