# BUG-1: TAX_RATE 是字符串而非 float，calculator 直接用它做乘法会触发 TypeError
# BUG-2: MAX_RETRY_COUNT 根本不存在，某文件 import 了这个名字

TAX_RATE = "0.08"              # BUG-1: should be float 0.08
DISCOUNT_THRESHOLD = 100.0
FREE_SHIPPING_THRESHOLD = 200.0
PLATFORM_FEE_RATE = 0.02
MAX_RETRIES = 3                # 正确常量，但 retry_helper 用的是不存在的 MAX_RETRY_COUNT

DATABASE_URL = "sqlite:///warehouse.db"
LOG_LEVEL = "INFO"
DEFAULT_CURRENCY = "USD"
REPORT_OUTPUT_DIR = "reports"