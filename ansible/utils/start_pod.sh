#!/bin/bash
# argv:
# $1: pod name
ansible-playbook -i inventory/local start_instances.yml -e pod=$1
