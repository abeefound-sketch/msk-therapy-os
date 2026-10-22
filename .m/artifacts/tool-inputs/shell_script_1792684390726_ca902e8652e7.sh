python3 -c "
import sqlite3, time
from msk_therapy_os.db import init_db, seed_db

db = sqlite3.connect(':memory:')
t0 = time.time()
init_db(db)
t1 = time.time()
print(f'init_db: {t1-t0:.4f}s')
seed_db(db)
t2 = time.time()
print(f'seed_db: {t2-t1:.4f}s')
"
