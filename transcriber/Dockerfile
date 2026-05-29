FROM public.ecr.aws/lambda/python:3.14

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY audio_utils.py ${LAMBDA_TASK_ROOT}
COPY s3_utils.py ${LAMBDA_TASK_ROOT}
COPY transcribe.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.handler" ]