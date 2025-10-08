import ssl
from http.cookiejar import DefaultCookiePolicy
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import Retry
from urllib3.util.ssl_ import create_urllib3_context


class TLSAdapter(HTTPAdapter):
    def __init__(self, ssl_options, **kwargs):
        self.ssl_options = ssl_options
        super(TLSAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = create_urllib3_context(cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)


class Session:
    def __init__(
        self,
        retry_on_failure: bool = True,
        retry: int = 20,
        backoff_factor: int = 20,
        change_tls_version: bool = False,
        user_agent: Optional[str] = None,
        status_forcelist_exemptions: list = [],
        disable_cookies: bool = False
    ):
        self.retry_on_failure = retry_on_failure
        self.retry = retry
        self.backoff_factor = backoff_factor
        self.change_tls_version = change_tls_version
        self.user_agent = user_agent
        self.status_forcelist_exemptions = status_forcelist_exemptions
        self.disable_cookies = disable_cookies

        self.prepare_status_forcelist()
        self.session()
        self.define_user_agent()

    def prepare_status_forcelist(self):
        default_status_forcelist = [104, 429, 403, 404, 500, 502, 503, 504, 524, 529]
        self.status_forcelist = [i for i in default_status_forcelist if i not in self.status_forcelist_exemptions]

    def session(self):
        self.s = requests.session()

        if self.disable_cookies is True:
            self.s.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))

        if self.retry_on_failure is True or self.change_tls_version is True:
            retry_method = Retry(
                total=self.retry,
                backoff_factor=self.backoff_factor,
                status_forcelist=self.status_forcelist
            )

            if self.retry_on_failure is True and self.change_tls_version is False:
                adapter = HTTPAdapter(max_retries=retry_method)
            elif self.retry_on_failure is True and self.change_tls_version is True:
                adapter = TLSAdapter(ssl.OP_NO_TLSv1, max_retries=retry_method)
            elif self.retry_on_failure is False and self.change_tls_version is True:
                adapter = TLSAdapter(ssl.OP_NO_TLSv1)
            self.s.mount('http://', adapter)
            self.s.mount('https://', adapter)

    def define_user_agent(self):
        if self.user_agent is None:
            self.user_agent = (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/114.0.0.0 Safari/537.36'
            )
