#!/bin/bash
# CheckTime is a free software developed by Tommaso Fontana for Würth Phoenix S.r.l. under GPL-2 License.

docker stop checktime-test-env
docker rm checktime-test-env

# "Build the container"
docker build --file test_env_dockerfile -t checktime-test-env .

# "Run the container"
docker run -it checktime-test-env 