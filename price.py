import json
import os

import pandas as pd

from browser import USwitchPrices
from common.datetime_config import DateTimeConfig
from common.graphql import query_get_result
from common.session import Session
from common.utils import safe_dict_get, _get_safe


class Prices(DateTimeConfig, Session):
    def __init__(self, post_code: str):
        DateTimeConfig.__init__(self)
        Session.__init__(self)
        self.post_code = post_code

    def get_cookies(self):
        self.browser_cookies = USwitchPrices(self.post_code).main()

        if self.browser_cookies is not None:
            for cookie in self.browser_cookies:
                self.s.cookies.set(cookie['name'], cookie['value'])

        self.cookies = self.s.cookies.get_dict()

    def _define_headers(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Accept': 'application/graphql-response+json, application/graphql+json, application/json, text/event-stream, multipart/mixed',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.uswitch.com/gas-electricity/journey/current-plan/?step=payment-gas',
            'ssid': self.cookies['ssid'],
            'uscd': self.cookies['uscd'],
            'account-session': '',
            'account-signedin': 'false',
            'x-is-server': 'false',
            'urefs': '',
            'rvu-brand': 'uswitch',
            'content-type': 'application/json',
            'Origin': 'https://www.uswitch.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
            'TE': 'trailers'
        }

    def get_plans(self):
        if not os.path.exists(f'output_json/response_{self.post_code.replace(" ", "_")}.json'):
            self.get_cookies()
            if self.browser_cookies is not None:
                self._define_headers()
                self.plans_api_response()
                self.parse_response()
                self.to_dataframe()
        else:
            with open(f'output_json/response_{self.post_code.replace(" ", "_")}.json', 'r') as f:
                self.response_data = json.load(f)
                self.parse_response()
                self.to_dataframe()

    def plans_api_response(self):
        url = 'https://www.uswitch.com/gas-electricity/graphql/'

        payload = json.dumps({
            "operationName": "GetResultsPageAstro",
            "query": query_get_result,
            "variables": {
                "evParams": {
                "filters": {
                    "fuel": "DUAL_FUEL",
                    "greenOnly": None,
                    "incentives": None,
                    "longTermFixed": None,
                    "noCancellationFee": None,
                    "onlyShowFulfillable": False,
                    "paperBilling": None,
                    "paymentMethod": "MONTHLY_DIRECT_DEBIT",
                    "rateType": "FIXED_OR_VARIABLE",
                    "warmHomeDiscount": None
                },
                "flagPriceCap": False,
                "limit": 2000,
                "newVariant": "EV",
                "offset": 0,
                "previewId": None
                },
                "params": {
                "filters": {
                    "fuel": "DUAL_FUEL",
                    "greenOnly": None,
                    "incentives": None,
                    "longTermFixed": None,
                    "noCancellationFee": None,
                    "onlyShowFulfillable": False,
                    "paperBilling": None,
                    "paymentMethod": "MONTHLY_DIRECT_DEBIT",
                    "rateType": "FIXED_OR_VARIABLE",
                    "warmHomeDiscount": None
                },
                "flagPriceCap": False,
                "limit": 200,
                "newVariant": None,
                "offset": 0,
                "previewId": None
                },
                "sessionId": self.cookies['ssid']
            }
        })

        response = self.s.post(url, headers=self.headers, data=payload)
        self.response_data = response.json()

        os.makedirs('output_json', exist_ok=True)
        with open(f'output_json/response_{self.post_code.replace(" ", "_")}.json', 'w') as f:
            json.dump(self.response_data, f)

    def parse_response(self):
        self.plans_data = [
            self.parse_plan(
                plan,
                supply_address=self.response_data['data']['session']['addressForId'],
                supply_address_full=self.response_data['data']['session']['supplyAddressFull'],
                meters=self.response_data['data']['session']['metersForAddress']
            )
            for plan
            in self.response_data['data']['session']['multiBillComparison']['comparisonPlans']
        ]

    def parse_plan(self, plan: dict, **kwargs) -> dict:
        electricity = plan.get('electricity', {}).get('til', {})
        electricity_tarrif = electricity.get('tariffRate', {})

        gas = plan.get('gas', {}).get('til', {})
        gas_tarrif = gas.get('tariffRate', {})

        info = {
            'input_post_code': self.post_code,
            'plan_position': plan['position'],
            'plan_id': plan['key'],
            'plan_name': plan['name'],
            'comparison_type': plan.get('comparisonType'),
            'is_fulfillable': plan.get('isFulfillable'),
            'is_cashback_eligible': plan.get('isCashbackEligible'),
            'supplier_id': plan.get('supplier', {}).get('key'),
            'supplier_name': plan.get('supplier', {}).get('name'),
            'duration_months': safe_dict_get(plan.get('rateGuarantee'), 'duration'),
            'electricity_price': electricity_tarrif[0].get('price'),
            'electricity_price_label': electricity_tarrif[0].get('rateLabel'),
            'electricity_exit_fee': _get_safe(electricity, 'exitFees', 'fee'),
            'electricity_tarrif': electricity_tarrif,
            'gas_price': gas_tarrif[0].get('price'),
            'gas_price_label': gas_tarrif[0].get('rateLabel'),
            'gas_exit_fee': _get_safe(gas, 'exitFees', 'fee'),
            'gas_tarrif': gas_tarrif,
            'payment_method': plan.get('paymentMethod'),
            'price_cap_applied': plan.get('priceCapApplied'),
            'tariff_type': plan.get('tariffType'),
            'exit_fees': _get_safe(plan, 'exitFees', 'fee'),
            **kwargs
        }

        return info

    def to_dataframe(self):
        df = pd.DataFrame(self.plans_data)

        os.makedirs('output', exist_ok=True)
        file_name = f'prices_{self.post_code.replace(" ", "_")}'
        df.to_parquet(f'output/{file_name}.parquet', index=False, engine='pyarrow')
        df.to_excel(f'output/{file_name}.xlsx', index=False, engine='openpyxl')

    def main(self):
        self.get_plans()
        self.to_dataframe()


if __name__ == '__main__':
    Prices('WS13 8PE').main()
