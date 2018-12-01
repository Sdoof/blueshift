# image for running as a container
# make sure we create the blueshift root workspace structure as well.

FROM python:3.6-alpine
COPY . /blueshift
WORKDIR /blueshift
RUN pip install -r requirements.txt
ENTRYPOINT ["blueshift"]
CMD ["--help"]