from time import sleep
from celery import Celery
from celery.result import AsyncResult
import os

app = Celery(__name__)

app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

if __name__ == "__main__":
    sleep(6)
    kwargs = {'case_id': 1}
    
    res = app.send_task(name="opt_pls", kwargs=kwargs, queue='opt_pls')
    id = res.task_id

    while (True):
        task_result = AsyncResult(id)

        if task_result.result != None:
            print(task_result.result)
            break
        else:
            print(f"ID: {id}. Status: {task_result.status}")
        
        sleep(60)
