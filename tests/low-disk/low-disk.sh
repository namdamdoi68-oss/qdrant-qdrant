#!/usr/bin/env bash

set -ex

cd "$(dirname "${BASH_SOURCE[0]}")"

declare DOCKER_IMAGE_NAME=qdrant/qdrant

docker buildx build --build-arg=PROFILE=ci --load ../../ --tag=$DOCKER_IMAGE_NAME

declare OOD_CONTAINER_NAME=qdrant-ood

container=$(docker run -d --name $OOD_CONTAINER_NAME --mount type=tmpfs,destination=/qdrant/storage,tmpfs-size=10M -p 6333:6333 $DOCKER_IMAGE_NAME)

function cleanup {
    docker rm -f "$container"
}
trap cleanup EXIT

while [[ $(curl -sS localhost:6333 -w '%{http_code}' -o /dev/null) != 200 ]]; do
    if ! docker ps | grep -q "$OOD_CONTAINER_NAME"; then
        echo "Container failed to start" >&2
        docker logs "$container"
        exit 1
    fi
done

# Check that low disk is handled OK during points insertion
# This also executes search after each insertion
python3 create_and_search_items.py low-disk 2000 6333

sleep 5

# Check that there's an OOD log message in service logs.
declare OUT_OF_DISK_MSG='No space left on device:'

if (! docker logs "$container" 2>&1 | grep "$OUT_OF_DISK_MSG") ; then
    echo "'$OUT_OF_DISK_MSG' log message not found in $container container logs" >&2
    exit 9
fi

echo "LOW DISK TEST PASSED SUCCESSFULLY!"
