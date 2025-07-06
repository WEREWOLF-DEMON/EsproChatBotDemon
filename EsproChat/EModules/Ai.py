# bard_ai.py

import aiohttp

async def get_bard_reply(prompt):
    try:
        short_prompt = f"Reply casually and briefly like a normal person: {prompt}"
        url = f"https://bardapi.dev/api/gemini?question={short_prompt}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data.get("content", "Kuch samajh nahi aaya 😅")
    except Exception:
        return "⚠️ AI se reply laate waqt error aaya."
