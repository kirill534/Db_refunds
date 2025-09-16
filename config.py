# support_app/config.py

CONN_DB = "dbname=work1 user=postgres password=0843 host=localhost port=5432"

# Связь листов и таблиц базы данных
SHEET_TO_TABLE = {
    "BTC - Bitcoin": "support_data_btc_-_bitcoin",
    "ETH - Ethereum": "support_data_eth_-_ethereum",
    "USDT (ERC-20)": "support_data_usdt_(erc-20)",
    "TRX - Tron": "support_data_trx_-_tron",
    "USDT (TRC-20)": "support_data_usdt_(trc-20)",
    "TON": "support_data_ton",
    "USDT (TON)": "support_data_usdt_(ton)",
    "USDC (ERC-20)": "support_data_usdc_(erc-20)"
}

# Токены по листам
TOKEN_MAPPING = {
    "BTC - Bitcoin": "BTC",
    "ETH - Ethereum": "ETH",
    "USDT (ERC-20)": "USDT (ETH)",
    "TRX - Tron": "TRX",
    "USDT (TRC-20)": "USDT (TRX)",
    "TON": "TON",
    "USDT (TON)": "USDT (TON)",
    "USDC (ERC-20)": "USDC (ETH)"
}

LIST_TOKEN = [
    "BTC - Bitcoin", "ETH - Ethereum", 
    "USDT (ERC-20)", "TRX - Tron",
    "USDT (TRC-20)", "TON", 
    "USDT (TON)", "USDC (ERC-20)"
]

# Поля формы
FIELDS = [
    "ФИО", "Номер", "Дата", "ID Клиента", "Сумма заявки", "Токен",
    "Сумма поступления", "Хэш", "Адрес отправителя", "Адрес возврата",
    "ХЭШ ВОЗВРАТА", "Возврат сделан (+)", "Причина возврата", "Статус"
]

ENG_FIELDS = [
    "fio", "number", "date", "user_id", "application_amount", "token",
    "receipt_amount", "hash", "sender_address", "return_address",
    "return_hash", "return_done", "return_reason", "status"
]

ENG_FIELDS_MEMO = (
    "fio", "number", "date", "user_id", "application_amount", "token",
    "receipt_amount", "hash", "sender_address", "return_address",
    "return_hash", "return_done", "return_reason", "status", "memo"
)

# Обязательные поля
REQUIRED_FIELDS = [
    "ФИО", "Номер", "Дата", "ID Клиента", "Токен", "Сумма поступления",
    "Хэш", "Адрес отправителя", "Адрес возврата", "Причина возврата"
]

# Неактивные поля
DISABLED_FIELDS = ["ХЭШ ВОЗВРАТА", "Возврат сделан (+)", "Статус", "Сумма заявки", "Мемо"]


FIELDS_TS_RU = [
    "№", "ФИО", "Номер", "Дата", "ID", "Сумма заявки", "Токен",
    "Сумма поступления", "Хэш", "Адрес отправителя", "Адрес возврата",
    "ХЭШ ВОЗВРАТА", "Возврат сделан (+)", "Причина возврата", "Статус"
]

FIELDS_TS_ENG = [
    "id", "fio", "number", "date", "user_id", "application_amount", "token",
    "receipt_amount", "hash", "sender_address", "return_address",
    "return_hash", "return_done", "return_reason", "status"
]

