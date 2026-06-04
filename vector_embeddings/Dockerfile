FROM public.ecr.aws/lambda/python:3.14

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY extract.py ${LAMBDA_TASK_ROOT}
COPY handler.py ${LAMBDA_TASK_ROOT}
COPY load.py ${LAMBDA_TASK_ROOT}
COPY transform.py ${LAMBDA_TASK_ROOT}

CMD [ "handler.lambda_handler" ]