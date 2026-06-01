FROM public.ecr.aws/lambda/python:3.14

RUN dnf install -y tar xz && \
    curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar xJ && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-*-amd64-static

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY audio_utils.py ${LAMBDA_TASK_ROOT}
COPY s3_utils.py ${LAMBDA_TASK_ROOT}
COPY transcribe.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.handler" ]