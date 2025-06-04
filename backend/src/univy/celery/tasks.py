from univy.celery.celery_univy import app
import time

@app.task
def add(x, y):
    print(f"Adding {x} and {y}")
    time.sleep(10)
    return x + y


@app.task
def mul(x, y):
    print(f"Multiplying {x} and {y}")
    time.sleep(10)
    return x * y


@app.task
def xsum(numbers):
    print(f"Summing {numbers}")
    time.sleep(10)
    return sum(numbers)