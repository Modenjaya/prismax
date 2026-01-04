apt update
apt install -y \
  libgbm1 \
  libnss3 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libxcomposite1 \
  libxrandr2 \
  libxdamage1 \
  libxkbcommon0 \
  libasound2

pip install playwright

playwright install chromium
