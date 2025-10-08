import datetime

import pytz


class DateTimeConfig:
    def __init__(self, timezone: str = 'UTC', date_format: str = '%Y-%m-%d'):
        self.timezone = timezone
        self.date_format = date_format
        self.datetime_config()
        self.previous_week_start_end()
        self.previous_month_start_end()

    def datetime_config(self):
        self.pytz_timezone = pytz.timezone(self.timezone)
        self.now = datetime.datetime.now(self.pytz_timezone)
        self.today = self.now.strftime(self.date_format)
        self.week_ago = (self.now - datetime.timedelta(days=7)).strftime(self.date_format)

    def get_current_timestamp(self) -> str:
        pytz_timezone = pytz.timezone(self.timezone)
        now = datetime.datetime.now(pytz_timezone)
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')

        return now_str

    def previous_week_start_end(self):
        """ Get Monday and Sunday of previous week """
        today = datetime.date.today()

        prev_week_monday = today - datetime.timedelta(days=today.weekday(), weeks=1)
        prev_week_sunday = today - datetime.timedelta(days=today.weekday() + 1)

        self.prev_week_monday_str = prev_week_monday.strftime(self.date_format)
        self.prev_week_sunday_str = prev_week_sunday.strftime(self.date_format)

    def previous_month_start_end(self):
        """ Get Monday and Sunday of previous week """
        today = datetime.date.today()

        this_month_first = today.replace(day=1)
        self.prev_month_last = this_month_first - datetime.timedelta(days=1)
        self.prev_month_first = self.prev_month_last.replace(day=1)

        self.prev_month_first_str = self.prev_month_first.strftime(self.date_format)
        self.prev_month_last_str = self.prev_month_last.strftime(self.date_format)
