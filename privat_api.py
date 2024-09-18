import platform
import aiohttp
import asyncio
from datetime import datetime, timedelta
import sys


class PrivatBankAPIClient:
    BASE_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='

    def __init__(self, days: int):
        if days > 10:
            raise ValueError("Максимальна кількість днів не може бути більшою за 10")
        self.days = days

    async def fetch_rates(self, session, date: str):
        url = f"{self.BASE_URL}{date}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    print(f"Помилка при отриманні даних для {date}: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Помилка мережі: {e}")
        return None

    async def get_exchange_rates(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(self.days):
                date = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
                tasks.append(self.fetch_rates(session, date))
            return await asyncio.gather(*tasks)


class CurrencyFilter:
    @staticmethod
    def filter_currency_rates(data):
        filtered_data = []
        for day_data in data:
            if day_data:
                date = day_data.get('date')
                exchange_rates = day_data.get('exchangeRate', [])
                daily_rates = {}
                for rate in exchange_rates:
                    if rate['currency'] == 'USD':
                        daily_rates['USD'] = {
                            'sale': rate.get('saleRate'),
                            'purchase': rate.get('purchaseRate')
                        }
                    elif rate['currency'] == 'EUR':
                        daily_rates['EUR'] = {
                            'sale': rate.get('saleRate'),
                            'purchase': rate.get('purchaseRate')
                        }
                if daily_rates:
                    filtered_data.append({date: daily_rates})
        return filtered_data


class CurrencyRateFetcher:
    def __init__(self, days: int):
        self.api_client = PrivatBankAPIClient(days)
        self.currency_filter = CurrencyFilter()

    async def fetch_and_display_rates(self):
        rates_data = await self.api_client.get_exchange_rates()
        filtered_data = self.currency_filter.filter_currency_rates(rates_data)
        print(filtered_data) 


async def main(days):
    fetcher = CurrencyRateFetcher(days)
    await fetcher.fetch_and_display_rates()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: <кількість_днів_до_10>")
        sys.exit(1)

    days = int(sys.argv[1])
    if days > 10:
        print("Кількість днів не може бути більшою за 10.")
        sys.exit(1)

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(days))
