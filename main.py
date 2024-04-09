import sys
import asyncio

from tg_client import rotate
from models import migrate

if __name__ == '__main__':
    try:
        if sys.argv[1] == 'rotate':
            if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            asyncio.run(rotate())
        if sys.argv[1] == 'migrate':
            migrate()
    except IndexError:
        print('error of argv')
