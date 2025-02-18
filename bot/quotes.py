import aiohttp
import logging

logger = logging.getLogger("bot.quotes")

async def get_random_quote(context):
    url = "https://favqs.com/api/qotd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get("quote", {}).get("body", "No quote found.")
                    author = data.get("quote", {}).get("author", "Unknown")
                    return f"\"{quote}\" - {author}"
                else:
                    logger.error(f"API returned an error: {response.status}")
                    return "Sorry, I couldn't fetch a quote right now."
    except Exception as e:
        logger.error(f"Error fetching the quote: {e}")
        return "Sorry, an error occurred while fetching a quote."
