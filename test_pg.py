import asyncio, asyncpg

async def main():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:6543/questpath')
        print('connected')
        await conn.close()
    except Exception as exc:
        print('error', exc)

asyncio.run(main())
