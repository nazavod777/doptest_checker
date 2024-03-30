import asyncio

import aiohttp
from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger
from pyuseragents import random as random_useragent

from utils import append_file, loader, get_proxy


class Checker:
    def __init__(self,
                 private_key: str) -> None:
        self.account, self.private_key = None, private_key

        try:
            self.account: LocalAccount = Account.from_key(private_key=private_key)

        except ValueError:
            logger.error(f'{private_key} | Wrong Private Key')

    def get_sign_hash(self) -> str:
        sign_message: str = self.account.sign_message(
            signable_message=encode_defunct(text=f'weareDOPdev{self.account.address.lower()}weareDOPdev')
        ).signature.hex()

        return sign_message

    async def check_drop_amount(self,
                                client: aiohttp.ClientSession,
                                sign_hash: str) -> float:
        while True:
            response_text: None = None

            try:
                r: aiohttp.ClientResponse = await client.post(
                    url='https://apiclaims.dop.org/auth/signin',
                    json={
                        'sign': sign_hash,
                        'walletAddress': self.account.address.lower()
                    },
                    headers={
                        'user-agent': random_useragent()
                    },
                    proxy=get_proxy()
                )

                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                if response_json['statusCode'] == 404:
                    logger.error(f'{self.private_key} | {response_json["message"]}')

                    async with asyncio.Lock():
                        await append_file(
                            file_path='result/404_response.txt',
                            file_content=f'{self.private_key}\n'
                        )

                    return 0

                elif response_json['statusCode'] == 429:
                    logger.info(f'{self.private_key} | {response_json["message"]}, sleeping 30 secs.')
                    await asyncio.sleep(delay=30)
                    continue

                return response_json['data']['user']['airdropAmount']

            except Exception as error:
                if response_text:
                    logger.error(f'{self.private_key} | Unexpected Error When Getting Drop Amount: {error}, '
                                 f'response: {response_text}')

                else:
                    logger.error(f'{self.private_key} | Unexpected Error When Getting Drop Amount: {error}')

    async def check_account(self,
                            client: aiohttp.ClientSession) -> None:
        if not self.account:
            async with asyncio.Lock():
                await append_file(
                    file_path='result/wrong_keys.txt',
                    file_content=f'{self.private_key}\n'
                )
            return

        sign_hash: str = self.get_sign_hash()
        drop_amount: float = await self.check_drop_amount(client=client,
                                                          sign_hash=sign_hash)

        if drop_amount > 0:
            logger.success(f'{self.private_key} | {drop_amount}')

            async with asyncio.Lock():
                loader.total_points += drop_amount

                await append_file(
                    file_path='result/eligible.txt',
                    file_content=f'{self.private_key} | {drop_amount}\n'
                )

        else:
            logger.error(f'{self.private_key} | {drop_amount}')


async def check_account(private_key: str,
                        client: aiohttp.ClientSession) -> None:
    await Checker(private_key=private_key).check_account(client=client)
