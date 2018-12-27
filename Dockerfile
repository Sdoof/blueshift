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
    && apk add --no-cache make cmake gcc g++ gfortran libffi openssl linux-headers openblas  lapack\
    && apk add --no-cache --virtual .build-deps  \
		libffi-dev openssl-dev build-base python3-dev\
		py3-pip \
        lapack-dev \
	&& pip install cython && pip install numpy && pip install setuptools-scm \
    # install talib
    && wget -O talib.tar.gz "http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz" \
    && mkdir -p /usr/src/talib \
    && tar -xzC /usr/src/talib --strip-components=1 -f talib.tar.gz \
    && rm talib.tar.gz \
    && cd /usr/src/talib \
    && ./configure \
        --prefix=/usr \
    && make && make install \
    # install blueshift and deps and some interesting packages
    && cd ${BLUESHIFT_DIR} \
    && pip install -r requirements.txt \
    && pip install scipy && pip install scikit-learn && pip install ta-lib \
    && pip install blueshift-${BLUESHIFT_VERSION}.tar.gz \
    # cleanup
    && apk del .build-deps \
    && rm -rf /usr/src/talib \
    && rm -f requirements.txt && rm -f blueshift-${BLUESHIFT_VERSION}.tar.gz

# fix the fxcmpy thread issue
RUN set -ex \
    && export fxcmpy=/usr/local/lib/python3.6/site-packages/fxcmpy/fxcmpy.py \
    && export lineno=`grep -n $fxcmpy -e "Thread(target=self.__connect__)" | cut -f1 -d:` \
    && sed -i "${lineno} a \ \ \ \ \ \ \ \ self.socket_thread.daemon = True" $fxcmpy

# set up user
RUN addgroup -S ${BLUESHIFT_USER} && adduser -S ${BLUESHIFT_USER} -G ${BLUESHIFT_USER}
USER blueshift

# initialize blueshift
RUN set -ex \
    && mkdir .blueshift \
    && blueshift config > .blueshift/.blueshift_config.json

CMD ["/bin/sh"]