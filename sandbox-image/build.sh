#!/bin/bash

#NOTE the subnet and gateway has to be specified for the current computer its running on
podman network create -d macvlan --subnet=$1 --gateway=$2 -o parent=enp5s0 rat-sandbox-macvlan

if type podman >/dev/null 2>&1; then
    podman build -t rat-machine-image . --no-cache
else
    docker build -t rat-machine-image . --no-cache
fi


