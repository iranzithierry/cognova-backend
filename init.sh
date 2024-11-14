prisma generate
echo "Prisma Generated"

sed -i.bak "s/'models\./'/" ./venv/lib/python3.*/site-packages/prisma/models.py
echo "Prisma Models Updated"

chmod +x ./bin/scraper
echo "Scraper Got Execution Permission"