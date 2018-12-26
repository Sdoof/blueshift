# image for running as a container
# make sure we create the blueshift root workspace structure as well.

FROM python:3.6-alpine

ENV PATH /usr/local/bin:$PATH
ENV BLUESHIFT_VERSION 0.0.1
ENV BLUESHIFT_DIR /home/blueshift
ENV BLUESHIFT_USER blueshift

# set up workdir
RUN mkdir -p ${BLUESHIFT_DIR}
COPY requirements.txt ${BLUESHIFT_DIR}/requirements.txt
COPY ./dist/blueshift-${BLUESHIFT_VERSION}.tar.gz ${BLUESHIFT_DIR}/blueshift-${BLUESHIFT_VERSION}.tar.gz
WORKDIR ${BLUESHIFT_DIR}

# install build-deps
RUN set -ex \
    && apk update \
    && apk add --no-cache make cmake gcc g++ gfortran libffi openssl linux-headers \
    && apk add --no-cache --virtual .build-deps  \
		libffi-dev openssl-dev build-base python3-dev\
		py3-pip \
	&& pip install cython && pip install numpy && pip install setuptools-scm \
    && pip install -r requirements.txt \
    && pip install blueshift-${BLUESHIFT_VERSION}.tar.gz \
    # cleanup
    && apk del .build-deps \
    && rm -f requirements.txt && rm -f blueshift-${BLUESHIFT_VERSION}.tar.gz

# set up user
RUN addgroup -S ${BLUESHIFT_USER} && adduser -S ${BLUESHIFT_USER} -G ${BLUESHIFT_USER}
USER blueshift

# initialize blueshift
RUN set -ex \
    && mkdir .blueshift \
    && blueshift config > .blueshift/.blueshift_config.json

CMD ["/bin/sh"]