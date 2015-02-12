#!/bin/bash
# argv:
# $1: pod name
ansible-playbook provision.yml -i pod_inventory/$1_pod -e pod=$1 \
    --vault-password-file vault-password.txt
