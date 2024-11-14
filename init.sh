prisma generate
echo "prisma generated"

sed -i.bak "s/'models\./'/" ./venv/lib/python3.12/site-packages/prisma/models.py
echo "prisma models updated"

chmod +x ./bin/scraper