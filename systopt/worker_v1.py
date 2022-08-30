import os
from time import sleep
from celery import Celery
from celery.result import AsyncResult

from app.opt_pls_v1 import OptPls
from app.clients.webapi import api_client

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

@celery.task(name="opt_pls", bind=True)
def opt_pls_task(self, **kwargs):
    web_task_id=self.request.id    
    case_id = kwargs['case_id']
    # create an opt object
    opt_pls = OptPls(case_id, web_task_id)
    tes_data = opt_pls.get_tes_input()
    print("sys_opt completed !!!")
    
    # Send task to SNT OPT
    kwargs = {'job_data': tes_data}
    res = celery.send_task(name="opt_snt", kwargs=kwargs, queue='opt_snt')
    opt_task_id = res.task_id
    print(f"Task sent. id: {opt_task_id}")

    # Waiting for result every second
    tes_result = None
    while (True):
        task_result = AsyncResult(opt_task_id)

        if task_result.result != None:
            tes_result = task_result.result
            break
        else:
            print(f"ID: {opt_task_id}. Status: {task_result.status}")
        sleep(60)

    # Post data to finish the task
    data = opt_pls.get_case_result(tes_result)
    # api_client.post_case_result(case_id, data)
    
    return data

if __name__ == "__main__":
    print (f"test worker")

