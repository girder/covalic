#!/bin/bash
# argv:
# $1: pod name
ansible-playbook -i inventory/local stop_pod_instances.yml -e pod=$1
