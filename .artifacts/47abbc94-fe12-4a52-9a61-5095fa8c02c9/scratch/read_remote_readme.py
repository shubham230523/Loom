import httpx
import asyncio

async def read_readme():
    url = "https://raw.githubusercontent.com/shubham230523/AIMastery/master/README.md"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            print(resp.text)
        else:
            # try main
            url = "https://raw.githubusercontent.com/shubham230523/AIMastery/main/README.md"
            resp = await client.get(url)
            print(resp.text)

if __name__ == "__main__":
    asyncio.run(read_readme())
